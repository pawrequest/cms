"""Core player: manages VLC processes and channel state."""

from __future__ import annotations

import subprocess
import sys
import threading
import time
from collections.abc import Sequence

from .channels import StreamQuality
from .config import CMSConfig, DEFAULT_GROUP, CHANNEL_GROUPS
from .tiling import VLC_DELAY_MS


class CMSPlayer:
    """Open and manage VLC instances for RTSP camera feeds.

    Example::

        player = CMSPlayer()
        player.open_group("front")
        player.upgrade_quality()   # switches to main stream on next reload
        player.reload()
        player.close_all()
    """

    def __init__(self, config: CMSConfig | None = None) -> None:
        self.config: CMSConfig = config or CMSConfig()
        self.stream_quality: StreamQuality = config.default_quality
        self._active_channels: list[int] = []
        self._processes: list[subprocess.Popen] = []

        self.open_group(DEFAULT_GROUP)

    # ------------------------------------------------------------------ #
    # Read-only state
    # ------------------------------------------------------------------ #

    @property
    def active_channels(self) -> list[int]:
        """Currently open channel numbers (snapshot copy)."""
        return list(self._active_channels)

    # ------------------------------------------------------------------ #
    # Channel control
    # ------------------------------------------------------------------ #

    def open_channel(self, channel: int) -> None:
        """Launch a single VLC instance for *channel*."""
        url = self.config.build_url(channel, quality=self.stream_quality)
        proc = subprocess.Popen([self.config.vlc_path, url])
        self._processes.append(proc)

    def open_and_tile_channels(self, channels: Sequence[int], tile: bool = True) -> None:
        """Launch VLC for every channel in *channels* and record them as active."""
        self._active_channels = list(channels)
        for ch in channels:
            self.open_channel(ch)

        if tile:
            self.tile_windows()

    def open_group(self, group: str) -> None:
        """Open a named channel group.

        Args:
            group: One of the keys in :data:`~cms.channels.CHANNEL_GROUPS`
                   (``"doors"``, ``"front"``, ``"office"``, ``"main"``, ``"all"``).

        Raises:
            KeyError: If *group* is not a known group name.
        """
        channels = CHANNEL_GROUPS[group.lower()]
        self.open_and_tile_channels(channels)

    def reload(self) -> None:
        """Close all VLC windows and reopen the active channels."""
        self.close_all()
        self.open_and_tile_channels(self._active_channels)

    # ------------------------------------------------------------------ #
    # Quality
    # ------------------------------------------------------------------ #

    def set_quality(self, quality: StreamQuality) -> None:
        """Set the stream quality. Does *not* reload automatically."""
        self.stream_quality = quality

    def upgrade_quality(self) -> None:
        """Switch to the main (high-quality) stream."""
        self.stream_quality = StreamQuality.HIGH

    def downgrade_quality(self) -> None:
        """Switch to the sub (low-quality) stream."""
        self.stream_quality = StreamQuality.LOW

    def toggle_quality(self) -> None:
        """Toggle between HIGH and LOW quality."""
        self.stream_quality = self.stream_quality.toggled()

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    def close_all(self) -> None:
        """Terminate all running VLC processes."""
        self._processes.clear()
        if sys.platform == 'win32':
            subprocess.run(
                ['taskkill', '/IM', 'vlc.exe', '/F'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            subprocess.run(
                ['pkill', '-f', 'vlc'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

    def tile_windows(self, timeout: float = 5.0, *, delay_ms: float = VLC_DELAY_MS) -> None:
        """Arrange all open VLC windows in a grid.

        Polls for up to *timeout* seconds waiting for VLC to create its
        windows, then tiles them across the work area.  Returns True on
        success.  No-op on non-Windows platforms.
        """
        from .tiling import tile_vlc_windows

        if delay_ms:
            time.sleep(delay_ms / 1000)
        pids = {p.pid for p in self._processes if p.poll() is None}

        threading.Thread(
            target=lambda: tile_vlc_windows(pids, timeout=timeout), daemon=True
        ).start()
