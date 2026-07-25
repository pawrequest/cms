"""Runtime configuration, resolved from environment variables with sensible defaults."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from .channels import StreamQuality


@dataclass
class CMSConfig:
    """All configuration needed to connect to an RTSP camera system and launch VLC.

    Values are resolved from environment variables at instantiation time, so you
    can override any of them afterwards::

        cfg = CMSConfig()
        cfg.rtsp_host = "192.168.2.10"
    """

    # RTSP credentials / address
    rtsp_user: str = field(default_factory=lambda: os.getenv('RTSP_USER'))
    rtsp_pass: str = field(default_factory=lambda: os.getenv('RTSP_PASS'))
    rtsp_host: str = field(default_factory=lambda: os.getenv('RTSP_HOST'))
    rtsp_port: int = 554

    # Channels
    channel_groups: dict[str, list[int]] = field(default_factory=dict[str, list[int]])
    default_group_name: str = ''

    @property
    def default_group(self) -> list[int]:
        return self.channel_groups[self.default_group_name]

    max_channel: int = 16

    # VLC
    vlc_path: str = field(
        default_factory=lambda: os.getenv(
            'VLC_PATH', r'C:\Program Files (x86)\VideoLAN\VLC\vlc.exe'
        )
    )

    # Stream tuning
    rtp_caching: int = 100
    default_quality: StreamQuality = StreamQuality.HIGH
    default_codec: str = 'H264'

    # storage
    path: Path | None = None

    # ------------------------------------------------------------------ #
    def build_url(
            self,
            channel: int,
            quality: StreamQuality | None = None,
    ) -> str:
        """Return a URL for *channel*.

        Args:
            channel: Camera channel number (1-based).
            quality: Stream quality. Falls back to :attr:`default_quality` when *None*.
        """
        s = self.default_quality.value if quality is None else quality.value
        return (
            f'rtsp://{self.rtsp_host}:{self.rtsp_port}'
            f'/user={self.rtsp_user}&password={self.rtsp_pass}'
            f'&channel={channel}&stream={s}.sdp'
            f'?real_stream--rtp-caching={self.rtp_caching}'
        )

    @classmethod
    def from_toml(cls, tomlfile: Path) -> CMSConfig:
        """Load configuration from a TOML file."""
        with open(tomlfile, 'rb') as f:
            data = tomllib.load(f)

        if 'default_quality' in data:
            data['default_quality'] = StreamQuality[data['default_quality']]

        data['path'] = tomlfile

        return cls(**data)


def default_config() -> CMSConfig:
    return CMSConfig.from_toml(Path(r'D:\prdev\tools\cms\default_conf.toml'))
