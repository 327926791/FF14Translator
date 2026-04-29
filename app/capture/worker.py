from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from PySide6.QtCore import QThread, Signal
from PIL import Image, ImageEnhance, ImageOps
from rapidfuzz import fuzz

from app.capture.screen_capture import ScreenCapturer, ScreenRect
from app.glossary.glossary import Glossary, protect_terms, restore_terms
from app.ocr.windows_ocr import WindowsOcr
from app.translate.base import BaseTranslator, TranslatorType, OllamaConfig
from app.translate.factory import TranslatorFactory


@dataclass(frozen=True)
class CaptureConfig:
    hwnd: Optional[int]
    roi_screen: Tuple[int, int, int, int]  # left, top, width, height (screen coords)
    fps: int = 3
    ocr_interval_ms: int = 750
    translator_type: str = "offline"  # 翻译器类型
    translator_config: Optional[dict] = None  # 翻译器配置（dict 格式）


class CaptureWorker(QThread):
    new_line = Signal(str)
    status = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._running = False
        self._cfg: Optional[CaptureConfig] = None

    def start_capture(self, cfg: CaptureConfig) -> None:
        self._cfg = cfg
        if not self.isRunning():
            self._running = True
            self.start()
        else:
            self._running = True

    def stop_capture(self) -> None:
        self._running = False

    def run(self) -> None:  # noqa: N802
        if self._cfg is None:
            return

        capturer = ScreenCapturer()
        ocr = WindowsOcr(language_tag="en")

        glossary_dir = Path("glossary")
        glossary_dir.mkdir(parents=True, exist_ok=True)
        for name in ("names.txt", "places.txt", "terms.txt"):
            p = glossary_dir / name
            if not p.exists():
                p.write_text("", encoding="utf-8")

        last_ocr_at = 0.0
        last_text_norm = ""
        recent_norm: list[str] = []

        # 创建翻译器
        translator: Optional[BaseTranslator] = None
        if self._cfg.translator_type != "offline" and self._cfg.translator_config:
            try:
                cfg_dict = self._cfg.translator_config
                cfg_dict['type'] = self._cfg.translator_type
                
                # 根据类型创建对应的配置对象
                from app.translate.base import OllamaConfig, DeepSeekConfig, BaiduConfig
                
                if self._cfg.translator_type == "ollama":
                    translator_cfg = OllamaConfig(**cfg_dict)
                elif self._cfg.translator_type == "deepseek":
                    translator_cfg = DeepSeekConfig(**cfg_dict)
                elif self._cfg.translator_type == "baidu":
                    translator_cfg = BaiduConfig(**cfg_dict)
                else:
                    translator_cfg = None
                
                if translator_cfg:
                    translator = TranslatorFactory.create(translator_cfg)
                    if translator:
                        self.status.emit(f"翻译器已加载：{self._cfg.translator_type}")
            except Exception as e:
                self.status.emit(f"加载翻译器失败：{e}")

        fps = max(1, int(self._cfg.fps))
        frame_sleep = 1.0 / fps

        self.status.emit("捕获线程已启动")

        while True:
            if not self._running:
                time.sleep(0.05)
                if not self._running:
                    break
                continue

            now = time.monotonic()
            if (now - last_ocr_at) * 1000.0 < float(self._cfg.ocr_interval_ms):
                time.sleep(frame_sleep)
                continue
            last_ocr_at = now

            try:
                left, top, width, height = self._cfg.roi_screen
                img = capturer.grab(ScreenRect(left=left, top=top, width=width, height=height))
                img_pp = _preprocess_for_ocr(img)
                text = asyncio.run(ocr.recognize_pil(img_pp))
            except Exception as e:
                self.status.emit(f"OCR/截图失败：{e}")
                time.sleep(0.5)
                continue

            text = _normalize_ocr_text(text)
            if not text:
                time.sleep(frame_sleep)
                continue

            # 去重：与上一条相似度过高就丢弃
            if last_text_norm and fuzz.ratio(text, last_text_norm) >= 92:
                time.sleep(frame_sleep)
                continue
            if any(fuzz.ratio(text, t) >= 92 for t in recent_norm[-5:]):
                time.sleep(frame_sleep)
                continue

            recent_norm.append(text)
            last_text_norm = text

            speaker, line = _parse_speaker_line(text)

            out = f"{speaker}：{line}" if speaker else line

            # 翻译（可选）
            if translator is not None:
                try:
                    glossary = Glossary.load_from_dir(glossary_dir)
                    protected, mapping = protect_terms(line, glossary.all_terms())
                    zh = translator.translate(speaker or "", protected)
                    zh = restore_terms(zh, mapping)
                    out = f"{out}\n  -> {zh}"
                except Exception as e:
                    self.status.emit(f"翻译失败（将只显示原文）：{e}")

            self.new_line.emit(out)

            time.sleep(frame_sleep)

        self.status.emit("捕获线程已停止")


def _preprocess_for_ocr(img: Image.Image) -> Image.Image:
    # 常见对白框：白字+描边。这里做一个温和的预处理，后续可在 UI 加参数调节。
    g = ImageOps.grayscale(img)
    g = ImageEnhance.Contrast(g).enhance(2.2)
    g = ImageEnhance.Sharpness(g).enhance(1.8)
    # 二值化
    bw = g.point(lambda p: 255 if p > 160 else 0)
    # 放大一点提升 OCR
    bw = bw.resize((bw.width * 2, bw.height * 2))
    return bw


def _normalize_ocr_text(text: str) -> str:
    s = (text or "").replace("\r", "\n")
    lines = [ln.strip() for ln in s.split("\n")]
    lines = [ln for ln in lines if ln]
    return " ".join(lines).strip()


def _parse_speaker_line(text: str) -> tuple[str, str]:
    # 简单规则：优先按 ':' 或 '：' 分割
    for sep in (":", "："):
        if sep in text:
            left, right = text.split(sep, 1)
            speaker = left.strip()
            line = right.strip()
            # 避免把整句误判成 speaker（比如 “Meanwhile: ...”）
            if 1 <= len(speaker) <= 32 and line:
                return speaker, line
    return "", text.strip()

