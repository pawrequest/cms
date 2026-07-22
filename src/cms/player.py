"""Core player: manages VLC processes and channel state."""
from __future__ import annotations

import subprocess
import sys
from collections.abc import Sequence

from .channels import CHANNEL_GROUPS, StreamQuality
from .config import CMSConfig


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
        self.stream_quality: StreamQuality = StreamQuality.LOW
        self._active_channels: list[int] = []

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
        url = self.config.build_url(channel, stream=self.stream_quality.value)
        subprocess.Popen([self.config.vlc_path, url])

    def open_channels(self, channels: Sequence[int]) -> None:
        """Launch VLC for every channel in *channels* and record them as active."""
        self._active_channels = list(channels)
        for ch in channels:
            self.open_channel(ch)

    def open_group(self, group: str) -> None:
        """Open a named channel group.

        Args:
            group: One of the keys in :data:`~cms.channels.CHANNEL_GROUPS`
                   (``"doors"``, ``"front"``, ``"office"``, ``"main"``, ``"all"``).

        Raises:
            KeyError: If *group* is not a known group name.
        """
        channels = CHANNEL_GROUPS[group.lower()]
        self.open_channels(channels)

    def reload(self) -> None:
        """Close all VLC windows and reopen the active channels."""
        self.close_all()
        self.open_channels(self._active_channels)

    # ------------------------------------------------------------------ #
    # Quality
    # ------------------------------------------------------------------ #

    def set_quality(self, quality: StreamQuality) -> None:
        """Set the stream quality. Does *not* reload automatically."""
        self.stream_quality = quality

    def upgrade_quality(self) -> StreamQuality:
        """Switch to the main (high-quality) stream. Returns the new quality."""
        self.stream_quality = StreamQuality.HIGH
        return self.stream_quality

    def downgrade_quality(self) -> StreamQuality:
        """Switch to the sub (low-quality) stream. Returns the new quality."""
        self.stream_quality = StreamQuality.LOW
        return self.stream_quality

    def toggle_quality(self) -> StreamQuality:
        """Toggle between HIGH and LOW quality. Returns the new quality."""
        self.stream_quality = self.stream_quality.toggled()
        return self.stream_quality

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    def close_all(self) -> None:
        """Terminate all running VLC processes."""
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/IM", "vlc.exe", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            subprocess.run(
                ["pkill", "-f", "vlc"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

