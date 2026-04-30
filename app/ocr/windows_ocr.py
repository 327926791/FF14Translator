from __future__ import annotations

import io
from typing import Optional

from PIL import Image


def _load_winrt():
    """
    Prefer the modern `winrt` package (winrt-Windows.* 3.x, Python 3.12+ native).
    Fall back to the older `winsdk` 1.x if winrt is not available.
    Returns (Language, OcrEngine, BitmapDecoder, DataWriter, InMemoryRandomAccessStream)
    """
    try:
        from winrt.windows.globalization import Language
        from winrt.windows.media.ocr import OcrEngine
        from winrt.windows.graphics.imaging import BitmapDecoder
        from winrt.windows.storage.streams import DataWriter, InMemoryRandomAccessStream
        return Language, OcrEngine, BitmapDecoder, DataWriter, InMemoryRandomAccessStream
    except ImportError:
        pass

    try:
        from winsdk.windows.globalization import Language
        from winsdk.windows.media.ocr import OcrEngine
        from winsdk.windows.graphics.imaging import BitmapDecoder
        from winsdk.windows.storage.streams import DataWriter, InMemoryRandomAccessStream
        return Language, OcrEngine, BitmapDecoder, DataWriter, InMemoryRandomAccessStream
    except ImportError:
        pass

    raise ImportError(
        "Windows OCR 需要安装 winrt 或 winsdk 包。\n"
        "请运行：pip install winrt-Windows.Media.Ocr winrt-Windows.Globalization "
        "winrt-Windows.Graphics.Imaging winrt-Windows.Storage.Streams winrt-Windows.Foundation"
    )


# 模块加载时就预检，把 import 错误暴露在主线程而非 OCR 线程
try:
    _WINRT_TYPES = _load_winrt()
    _WINRT_AVAILABLE = True
except ImportError as _e:
    _WINRT_TYPES = None  # type: ignore[assignment]
    _WINRT_AVAILABLE = False
    _WINRT_IMPORT_ERROR = str(_e)


class WindowsOcr:
    """
    使用 Windows 自带 OCR（通过 winrt / winsdk 包调用）。

    优先使用现代 winrt 包（3.x），回退到旧版 winsdk（1.x）。
    引擎懒加载：首次调用 recognize_pil 时初始化。
    """

    def __init__(self, language_tag: str = "en") -> None:
        self.language_tag = language_tag
        self._engine = None

    def _ensure_engine(self) -> None:
        if self._engine is not None:
            return
        if not _WINRT_AVAILABLE:
            raise RuntimeError(_WINRT_IMPORT_ERROR)

        Language, OcrEngine, *_ = _WINRT_TYPES
        lang = Language(self.language_tag)
        self._engine = OcrEngine.try_create_from_language(lang)
        if self._engine is None:
            raise RuntimeError(
                f"Windows OCR 引擎不支持语言：{self.language_tag}。\n"
                "请在「Windows 设置 → 时间和语言 → 语言」中安装英语语言包（English）。"
            )

    async def recognize_pil(self, img: Image.Image) -> str:
        self._ensure_engine()

        _, _, BitmapDecoder, DataWriter, InMemoryRandomAccessStream = _WINRT_TYPES

        if img.mode != "RGB":
            img = img.convert("RGB")

        bio = io.BytesIO()
        img.save(bio, format="PNG")
        data = bio.getvalue()

        stream = InMemoryRandomAccessStream()
        writer = DataWriter(stream)
        writer.write_bytes(data)
        await writer.store_async()
        await writer.flush_async()
        writer.detach_stream()
        stream.seek(0)

        decoder = await BitmapDecoder.create_async(stream)
        sb = await decoder.get_software_bitmap_async()
        result = await self._engine.recognize_async(sb)
        return (result.text or "").strip()


def try_create_windows_ocr() -> Optional[WindowsOcr]:
    try:
        ocr = WindowsOcr(language_tag="en")
        ocr._ensure_engine()
        return ocr
    except Exception:
        return None
