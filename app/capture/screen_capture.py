from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import mss
from PIL import Image


@dataclass(frozen=True)
class ScreenRect:
    left: int
    top: int
    width: int
    height: int

    def to_mss(self) -> dict:
        return {"left": self.left, "top": self.top, "width": self.width, "height": self.height}


class ScreenCapturer:
    def __init__(self) -> None:
        self._sct = mss.mss()

    def grab(self, rect: ScreenRect) -> Image.Image:
        raw = self._sct.grab(rect.to_mss())
        img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
        return img

