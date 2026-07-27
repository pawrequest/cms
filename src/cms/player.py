"""Core player: manages VLC processes and channel state."""

from __future__ import annotations

import logging
import subprocess
from collections.abc import Sequence

from .channels import StreamQuality
from .config import CMSConfig
from .tiling import Tiler

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
        self.config: CMSConfig = config
        self.stream_quality: StreamQuality = config.default_quality
        self._active_channels: list[int] = []
        self._processes: list[subprocess.Popen] = []
        self.tiler = Tiler(self._processes)
        log.debug('CMSPlayer init — quality=%s initial_group=%s', self.stream_quality, config.initial_group_name)

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
                '--qt-minimal-view',  # hide control bar / scrubber
                '--no-video-title-show',  # suppress OSD title overlay
            ]
        log.debug('Launching VLC for channel %d', channel)
        proc = subprocess.Popen(cmd)
        self._processes.append(proc)

    def open_channels(self, channels: Sequence[int]) -> None:
        """Launch VLC for every channel in *channels* and record them as active."""
        log.debug('open_channels: channels=%s', list(channels))
        sorted_channels = sorted(list(channels), reverse=True)
        self._active_channels = sorted_channels
        for ch in sorted_channels:
            self.open_channel(ch)

    def open_group(self, group: str) -> None:
        """Open a named channel group.

        Args:
            group: Name of a channel group (case-insensitive).

        Raises:
            KeyError: If *group* is not a known group name.
        """
        log.debug('open_group: %r', group)
        channels = self.config.channel_groups[group.lower()]
        self.open_channels(channels)

    def reload(self) -> None:
        """Close all VLC windows and reopen the active channels."""
        log.debug('reload: active_channels=%s', self._active_channels)
        self.close_all()
        self.open_channels(self._active_channels)

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
