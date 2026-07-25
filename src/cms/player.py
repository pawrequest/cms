"""Core player: manages VLC processes and channel state."""

from __future__ import annotations

import logging
import subprocess
import threading
import time
from collections.abc import Sequence

from .channels import StreamQuality
from .config import CMSConfig
from .tiling import VLC_DELAY_MS

log = logging.getLogger(__name__)


class CMSPlayer:
    """Open and manage VLC instances for RTSP camera feeds.

    Example::

        player = CMSPlayer()
        player.open_group("front")
        player.upgrade_quality()   # switches to main stream on next reload
        player.reload()
        player.close_all()
    """

    def __init__(self, config: CMSConfig = None) -> None:
        config = config or CMSConfig()
        self.config = config
        self.stream_quality: StreamQuality = config.default_quality
        self._active_channels: list[int] = []
        self._processes: list[subprocess.Popen] = []
        log.debug('CMSPlayer init — quality=%s initial_group=%s', self.stream_quality, config.initial_group_name)
        self.open_group(self.config.initial_group_name)

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
        cmd = [self.config.vlc_path, url]
        if self.config.minimal_view:
            cmd += [
                '--qt-minimal-view',     # hide control bar / scrubber
                '--no-video-title-show', # suppress OSD title overlay
            ]
        log.debug('Launching VLC for channel %d: %s', channel, url)
        proc = subprocess.Popen(cmd)
        self._processes.append(proc)

    def open_and_tile_channels(self, channels: Sequence[int], tile: bool = True) -> None:
        """Launch VLC for every channel in *channels* and record them as active."""
        log.debug('open_and_tile_channels: channels=%s tile=%s', list(channels), tile)
        self._active_channels = list(channels)
        for ch in channels:
            self.open_channel(ch)

        if tile:
            self.tile_windows()

    def open_group(self, group: str) -> None:
        """Open a named channel group.

        Args:
            group: Name of a channel group (case-insensitive).

        Raises:
            KeyError: If *group* is not a known group name.
        """
        log.debug('open_group: %r', group)
        channels = self.config.channel_groups[group.lower()]
        self.open_and_tile_channels(channels)

    def reload(self) -> None:
        """Close all VLC windows and reopen the active channels."""
        log.debug('reload: active_channels=%s', self._active_channels)
        self.close_all()
        self.open_and_tile_channels(self._active_channels)

    # ------------------------------------------------------------------ #
    # Quality
    # ------------------------------------------------------------------ #

    def set_quality(self, quality: StreamQuality) -> None:
        """Set the stream quality. Does *not* reload automatically."""
        log.debug('set_quality: %s', quality)
        self.stream_quality = quality

    def upgrade_quality(self) -> None:
        """Switch to the main (high-quality) stream."""
        log.debug('upgrade_quality → HIGH')
        self.stream_quality = StreamQuality.HIGH

    def downgrade_quality(self) -> None:
        """Switch to the sub (low-quality) stream."""
        log.debug('downgrade_quality → LOW')
        self.stream_quality = StreamQuality.LOW

    def toggle_quality(self) -> None:
        """Toggle between HIGH and LOW quality."""
        self.stream_quality = self.stream_quality.toggled()
        log.debug('toggle_quality → %s', self.stream_quality)

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    def close_all(self) -> None:
        """Terminate all running VLC processes."""
        log.debug('close_all: terminating %d process(es)', len(self._processes))
        for proc in self._processes:
            if proc.poll() is None:
                proc.terminate()
        self._processes.clear()

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
