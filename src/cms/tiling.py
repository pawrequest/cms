"""Tile VLC windows into a grid using the Win32 API (Windows only)."""

from __future__ import annotations

import ctypes
import ctypes.wintypes
import logging
import math
import sys
import threading
import time
from subprocess import Popen

VLC_DELAY_MS = 2000

log = logging.getLogger(__name__)


def _grid(n: int) -> tuple[int, int]:
    """Return (cols, rows) for an n-window grid, biased towards landscape."""
    cols = math.ceil(math.sqrt(n))
    rows = math.ceil(n / cols)
    return cols, rows


# ------------------------------------------------------------------ #
# Grid layout
# ------------------------------------------------------------------ #


def tile_hwnds(hwnds: set[int]) -> bool:
    """Arrange *hwnds* in a grid that fills the work area.

    Returns ``True`` if at least one window was positioned.
    """

    log.debug('Tiler.tile: hwnds=%s', hwnds)

    if sys.platform != 'win32' or not hwnds:
        return False

    user32 = ctypes.windll.user32

    work = ctypes.wintypes.RECT()
    user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(work), 0)  # SPI_GETWORKAREA
    screen_w = work.right - work.left
    screen_h = work.bottom - work.top

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


def tile_windows(pids: set[int], timeout: float = 5.0, extra_hwnds: list[int] | None = None) -> bool:
    """Find windows owned by *pids* and arrange them in a grid.

    Polls until every expected window is visible or *timeout* seconds elapse.
    Returns True if at least one window was tiled.
    """
    if sys.platform != 'win32':
        return False

    user32 = ctypes.windll.user32
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)

    def _find() -> list[int]:
        found: list[int] = []

        def _cb(hwnd: int, _: int) -> bool:
            if not user32.IsWindowVisible(hwnd):
                return True
            pid = ctypes.wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value not in pids:
                return True
            r = ctypes.wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(r))
            if (r.right - r.left) > 50 and (r.bottom - r.top) > 50:
                found.append(hwnd)
            return True  # keep enumerating — collect one window per pid

        user32.EnumWindows(EnumWindowsProc(_cb), 0)
        return found

    deadline = time.monotonic() + timeout
    hwnds = set(extra_hwnds) if extra_hwnds else set()
    while time.monotonic() < deadline:
        hwnds.update(_find())
        if len(hwnds) >= len(pids):
            break
        time.sleep(0.25)

    return tile_hwnds(hwnds)


# ------------------------------------------------------------------ #
# Tiler class
# ------------------------------------------------------------------ #


class Tiler:
    """Derives window positions from a shared process list and tiles them.

    Takes a **reference** to the player's process list so it always reflects
    the current set of live processes without any manual synchronisation.

    Example::

        tiler = Tiler(player._processes)
        tiler.tile()   # call after launching channels
    """

    def __init__(self, procs: list[Popen], pinned_hwnds: set[int] = None) -> None:
        self._procs = procs  # shared reference — owned by CMSPlayer
        self.pinned_hwnds = set(pinned_hwnds) if pinned_hwnds is not None else set()

    def pin_hwnd(self, hwnd: int) -> None:
        """Add a window handle to the pinned set, which is tiled along with
        the windows owned by the managed processes."""
        self.pinned_hwnds.add(hwnd)

    # ------------------------------------------------------------------ #
    # Tiling
    # ------------------------------------------------------------------ #

    def add_self(self):
        self.pinned_hwnds.add(ctypes.windll.user32.GetForegroundWindow())

    def tile(self, timeout: float = 5.0, *, delay_ms: float = VLC_DELAY_MS, extra_hwnds: list[int] = None) -> None:
        """Arrange all managed windows in a grid.

        Sleeps *delay_ms* milliseconds first to let VLC finish initialising
        (Qt apps reach an input-idle state before the main window is fully
        sized, so a fixed delay is more reliable than WaitForInputIdle here).
        Then polls for up to *timeout* seconds for all windows to appear.
        Runs entirely in a background thread — does not block the caller.
        """
        # Snapshot PIDs now; the list may change if close_all is called.
        pids = {p.pid for p in self._procs if p.poll() is None}

        delay = len(pids) * 0.3
        delay = max(delay, VLC_DELAY_MS / 1000)
        log.debug('Tiler.tile: calculated delay=%s seconds', delay)

        def _run() -> None:
            if delay_ms:
                time.sleep(delay)
                # time.sleep(delay_ms / 1000)
            tile_windows(pids, timeout=timeout, extra_hwnds=extra_hwnds)

        threading.Thread(target=_run, daemon=True).start()
