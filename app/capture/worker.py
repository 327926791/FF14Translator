from __future__ import annotations

import asyncio
import time
from collections import deque, OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from PySide6.QtCore import QThread, Signal
from PIL import Image, ImageEnhance, ImageOps
from rapidfuzz import fuzz

from app.capture.screen_capture import ScreenCapturer, ScreenRect
from app.glossary.glossary import Glossary, protect_terms, restore_terms
from app.ocr.windows_ocr import WindowsOcr
from app.translate.base import (
    BaseTranslator,
    OllamaConfig,
    DeepSeekConfig,
    QwenConfig,
    QwenMtConfig,
    BaiduConfig,
)
from app.translate.factory import TranslatorFactory


_TRANSLATION_CACHE_MAX = 200

# 这些后端不支持 system prompt，无法使用占位符术语保护
_NO_PLACEHOLDER_BACKENDS = frozenset({"baidu", "qwen_mt"})


class _LRUCache:
    """简单的 LRU 缓存，避免重复翻译相同文本。"""

    def __init__(self, maxsize: int = _TRANSLATION_CACHE_MAX) -> None:
        self._maxsize = maxsize
        self._cache: OrderedDict[str, str] = OrderedDict()

    def get(self, key: str) -> Optional[str]:
        if key not in self._cache:
            return None
        self._cache.move_to_end(key)
        return self._cache[key]

    def put(self, key: str, value: str) -> None:
        if key in self._cache:
            self._cache.move_to_end(key)
        else:
            if len(self._cache) >= self._maxsize:
                self._cache.popitem(last=False)
            self._cache[key] = value


@dataclass(frozen=True)
class CaptureConfig:
    hwnd: Optional[int]
    roi_screen: Tuple[int, int, int, int]  # left, top, width, height (screen coords)
    fps: int = 3
    ocr_interval_ms: int = 750
    translator_type: str = "offline"
    translator_config: Optional[dict] = None


def _build_translator(
    translator_type: str, translator_config: Optional[dict]
) -> Optional[BaseTranslator]:
    """根据类型和配置构建翻译器，失败返回 None。"""
    if translator_type == "offline" or not translator_config:
        return None
    cfg_data = dict(translator_config)  # 复制，不修改原 dict
    cfg_data["type"] = translator_type
    try:
        if translator_type == "ollama":
            cfg = OllamaConfig(**cfg_data)
        elif translator_type == "deepseek":
            cfg = DeepSeekConfig(**cfg_data)
        elif translator_type == "qwen":
            cfg = QwenConfig(**cfg_data)
        elif translator_type == "qwen_mt":
            cfg = QwenMtConfig(**cfg_data)
        elif translator_type == "baidu":
            cfg = BaiduConfig(**cfg_data)
        else:
            return None
        return TranslatorFactory.create(cfg)
    except Exception as e:
        print(f"[worker] 创建翻译器失败：{e}")
        return None


class CaptureWorker(QThread):
    new_line = Signal(str)
    status = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._running = False
        self._cfg: Optional[CaptureConfig] = None

    def start_capture(self, cfg: CaptureConfig) -> None:
        if self.isRunning():
            self._running = False
            self.wait(3000)
        self._cfg = cfg
        self._running = True
        self.start()

    def stop_capture(self) -> None:
        self._running = False

    def run(self) -> None:  # noqa: N802
        if self._cfg is None:
            return

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        capturer = ScreenCapturer()
        ocr = WindowsOcr(language_tag="en")

        glossary_dir = Path("glossary")
        glossary_dir.mkdir(parents=True, exist_ok=True)
        for name in ("names.txt", "places.txt", "terms.txt"):
            p = glossary_dir / name
            if not p.exists():
                p.write_text("", encoding="utf-8")

        glossary = Glossary.load_from_dir(glossary_dir)

        last_ocr_at = 0.0
        last_text_norm = ""
        recent_norm: deque[str] = deque(maxlen=20)

        translator = _build_translator(self._cfg.translator_type, self._cfg.translator_config)
        if translator is not None:
            self.status.emit(f"翻译器已加载：{self._cfg.translator_type}")

        translation_cache = _LRUCache()
        use_placeholder = self._cfg.translator_type not in _NO_PLACEHOLDER_BACKENDS

        fps = max(1, int(self._cfg.fps))
        frame_sleep = 1.0 / fps

        self.status.emit("捕获线程已启动")

        try:
            while self._running:
                now = time.monotonic()
                if (now - last_ocr_at) * 1000.0 < float(self._cfg.ocr_interval_ms):
                    time.sleep(frame_sleep)
                    continue
                last_ocr_at = now

                try:
                    left, top, width, height = self._cfg.roi_screen
                    img = capturer.grab(ScreenRect(left=left, top=top, width=width, height=height))
                    img_pp = _preprocess_for_ocr(img)
                    text = loop.run_until_complete(ocr.recognize_pil(img_pp))
                except Exception as e:
                    self.status.emit(f"OCR/截图失败：{e}")
                    time.sleep(0.5)
                    continue

                text = _normalize_ocr_text(text)
                if not text:
                    time.sleep(frame_sleep)
                    continue

                if last_text_norm and fuzz.ratio(text, last_text_norm) >= 92:
                    time.sleep(frame_sleep)
                    continue
                if any(fuzz.ratio(text, t) >= 92 for t in recent_norm):
                    time.sleep(frame_sleep)
                    continue

                recent_norm.append(text)
                last_text_norm = text

                speaker, line = _parse_speaker_line(text)
                out = f"{speaker}：{line}" if speaker else line

                if translator is not None:
                    cache_key = f"{speaker}\x00{line}"
                    zh = translation_cache.get(cache_key)
                    if zh is None:
                        try:
                            if use_placeholder:
                                protected, mapping = protect_terms(line, glossary.all_terms())
                                zh = translator.translate(speaker or "", protected)
                                zh = restore_terms(zh, mapping)
                            else:
                                zh = translator.translate(speaker or "", line)
                            translation_cache.put(cache_key, zh)
                        except Exception as e:
                            self.status.emit(f"翻译失败（将只显示原文）：{e}")
                            zh = None
                    if zh:
                        out = f"{out}\n  -> {zh}"

                self.new_line.emit(out)
                time.sleep(frame_sleep)
        finally:
            loop.close()
            self.status.emit("捕获线程已停止")


def _preprocess_for_ocr(img: Image.Image) -> Image.Image:
    g = ImageOps.grayscale(img)
    g = ImageEnhance.Contrast(g).enhance(2.2)
    g = ImageEnhance.Sharpness(g).enhance(1.8)
    bw = g.point(lambda p: 255 if p > 160 else 0)
    bw = bw.resize((bw.width * 2, bw.height * 2))
    return bw


def _normalize_ocr_text(text: str) -> str:
    s = (text or "").replace("\r", "\n")
    lines = [ln.strip() for ln in s.split("\n")]
    lines = [ln for ln in lines if ln]
    return " ".join(lines).strip()


def _parse_speaker_line(text: str) -> tuple[str, str]:
    for sep in (":", "："):
        if sep in text:
            left, right = text.split(sep, 1)
            speaker = left.strip()
            line = right.strip()
            if 1 <= len(speaker) <= 32 and line:
                return speaker, line
    return "", text.strip()
