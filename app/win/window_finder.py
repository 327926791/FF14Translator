from __future__ import annotations

from dataclasses import dataclass
from typing import List

import ctypes
from ctypes import wintypes


user32 = ctypes.WinDLL("user32", use_last_error=True)


@dataclass(frozen=True)
class WinInfo:
    hwnd: int
    title: str


def _get_window_text(hwnd: int) -> str:
    length = user32.GetWindowTextLengthW(hwnd)
    if length <= 0:
        return ""
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    return buf.value


def _is_window_visible(hwnd: int) -> bool:
    return bool(user32.IsWindowVisible(hwnd))


def find_ffxiv_windows() -> List[WinInfo]:
    """
    粗略查找 FFXIV 窗口（按标题关键字）。
    不保证 100% 命中：不同语言/启动器/覆盖层可能改变窗口标题。
    """

    results: List[WinInfo] = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def enum_proc(hwnd: int, lparam: int) -> bool:
        if not _is_window_visible(hwnd):
            return True
        title = _get_window_text(hwnd).strip()
        if not title:
            return True
        low = title.lower()
        if "final fantasy xiv" in low or "ffxiv" in low:
            results.append(WinInfo(hwnd=int(hwnd), title=title))
        return True

    user32.EnumWindows(enum_proc, 0)
    # 排个序：标题更像游戏本体的靠前
    results.sort(key=lambda w: (0 if "final fantasy xiv" in w.title.lower() else 1, w.title))
    return results

