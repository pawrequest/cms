"""Tile VLC windows into a grid using the Win32 API (Windows only)."""

from __future__ import annotations

import ctypes
import ctypes.wintypes
import math
import sys
import time

VLC_DELAY_MS = 1600


def _grid(n: int) -> tuple[int, int]:
    """Return (cols, rows) for an n-window grid, biased towards landscape."""
    cols = math.ceil(math.sqrt(n))
    rows = math.ceil(n / cols)
    return cols, rows


def tile_vlc_windows(pids: set[int], timeout: float = 5.0) -> bool:
    """Find VLC windows owned by *pids* and arrange them in a grid.

    Polls until every expected window is visible or *timeout* seconds elapse.
    Returns True if at least one window was tiled.
    """
    if sys.platform != 'win32' or not pids:
        return False

    user32 = ctypes.windll.user32

    # Work area — respects taskbar position
    work = ctypes.wintypes.RECT()
    user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(work), 0)  # SPI_GETWORKAREA
    screen_w = work.right - work.left
    screen_h = work.bottom - work.top

    EnumWindowsProc = ctypes.WINFUNCTYPE(
        ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM
    )

    def _find() -> list[int]:
        found: list[int] = []

        def _cb(hwnd: int, _: int) -> bool:
            if not user32.IsWindowVisible(hwnd):
                return True
            # Match window to one of our PIDs
            pid = ctypes.wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value not in pids:
                return True
            # Skip tiny/initialising windows
            r = ctypes.wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(r))
            if (r.right - r.left) > 50 and (r.bottom - r.top) > 50:
                found.append(hwnd)
            return True

        user32.EnumWindows(EnumWindowsProc(_cb), 0)
        return found

    # Poll until all windows are up
    deadline = time.monotonic() + timeout
    hwnds: list[int] = []
    while time.monotonic() < deadline:
        hwnds = _find()
        if len(hwnds) >= len(pids):
            break
        time.sleep(0.25)

    if not hwnds:
        return False

    n = len(hwnds)
    cols, rows = _grid(n)
    cell_w = screen_w // cols
    cell_h = screen_h // rows

    SWP_NOZORDER = 0x0004

    for i, hwnd in enumerate(hwnds):
        col = i % cols
        row = i // cols
        x = work.left + col * cell_w
        y = work.top + row * cell_h
        user32.SetWindowPos(hwnd, 0, x, y, cell_w, cell_h, SWP_NOZORDER)

    return True
