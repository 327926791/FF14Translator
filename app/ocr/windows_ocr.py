from __future__ import annotations

import io
from typing import Optional

from PIL import Image


class WindowsOcr:
    """
    使用 Windows 自带 OCR（通过 winsdk 包调用）。

    说明：
    - 这是 MVP 的“尽量免装大依赖”方案；
    - 仍然需要 `pip install winsdk`；
    - 若系统/环境不支持，会抛出异常，UI 会提示你改用其它 OCR 方案（后续可加 Tesseract/Paddle）。
    """

    def __init__(self, language_tag: str = "en") -> None:
        self.language_tag = language_tag
        self._engine = None

    def _ensure_engine(self) -> None:
        if self._engine is not None:
            return
        try:
            from winsdk.windows.globalization import Language
            from winsdk.windows.media.ocr import OcrEngine
        except ImportError as e:
            raise RuntimeError(
                f"winsdk not installed. Install it with: pip install winsdk\n"
                f"Original error: {e}"
            )

        lang = Language(self.language_tag)
        self._engine = OcrEngine.try_create_from_language(lang)
        if self._engine is None:
            raise RuntimeError(f"Windows OCR engine unavailable for language: {self.language_tag}")

    async def recognize_pil(self, img: Image.Image) -> str:
        self._ensure_engine()

        from winsdk.windows.graphics.imaging import BitmapDecoder
        from winsdk.windows.storage.streams import DataWriter, InMemoryRandomAccessStream

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
        return WindowsOcr(language_tag="en")
    except Exception:
        return None

