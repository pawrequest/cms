"""Runtime configuration, resolved from environment variables with sensible defaults."""

from __future__ import annotations

import logging
import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from .channels import StreamQuality


@dataclass
class CMSConfig:
    # RTSP credentials / address
    rtsp_user: str = field(default_factory=lambda: os.getenv('RTSP_USER'))
    rtsp_pass: str = field(default_factory=lambda: os.getenv('RTSP_PASS'))
    rtsp_host: str = field(default_factory=lambda: os.getenv('RTSP_HOST'))
    rtsp_port: int = 554

    # Channels
    channels: dict[int, str] = field(default_factory=dict)
    max_channel: int = 16
    channel_groups: dict[str, list[int]] = field(default_factory=dict)
    initial_group_name: str = ''

    def __post_init__(self):
        self.channel_groups.setdefault('all', self.all_channels)

    @property
    def all_channels(self) -> list[int]:
        return list(self.channels.keys()) if self.channels \
            else list(range(1, self.max_channel + 1))

    @property
    def initial_group(self) -> list[int]:
        return self.channel_groups[self.initial_group_name] if self.initial_group_name \
            else list(self.channels.values())[0] if self.channels \
            else self.all_channels

    # VLC
    vlc_path: str = field(
        default_factory=lambda: os.getenv(
            'VLC_PATH', r'C:\Program Files (x86)\VideoLAN\VLC\vlc.exe'
        )
    )
    minimal_view: bool = True  # hide controls/menu bar (--qt-minimal-view)

    # Stream tuning
    rtp_caching: int = 100
    default_quality: StreamQuality = StreamQuality.HIGH
    default_codec: str = 'H264'

    config_toml: Path | None = None

    # Debug / logging
    debug: bool = True

    url_template: str = field(
        default_factory=lambda: (
            "rtsp://{rtsp_host}:{rtsp_port}"
            "/user={rtsp_user}&password={rtsp_pass}"
            "&channel={channel}&stream={stream}.sdp"
            "?real_stream--rtp-caching={rtp_caching}"
        )
    )

    def build_url(self, channel: int, quality: StreamQuality | None = None) -> str:
        s = (self.default_quality if quality is None else quality).value
        return self.url_template.format_map(
            {
                'rtsp_host': self.rtsp_host,
                'rtsp_port': self.rtsp_port,
                'rtsp_user': self.rtsp_user,
                'rtsp_pass': self.rtsp_pass,
                'channel': channel,
                'stream': s,
                'rtp_caching': self.rtp_caching,
            }
        )

    # def build_url1(
    #         self,
    #         channel: int,
    #         quality: StreamQuality | None = None,
    # ) -> str:
    #     """Return a URL for *channel*.
    #
    #     Args:
    #         channel: Camera channel number (1-based).
    #         quality: Stream quality. Falls back to :attr:`default_quality` when *None*.
    #     """
    #     s = self.default_quality.value if quality is None else quality.value
    #     return (
    #         f'rtsp://{self.rtsp_host}:{self.rtsp_port}'
    #         f'/user={self.rtsp_user}&password={self.rtsp_pass}'
    #         f'&channel={channel}&stream={s}.sdp'
    #         f'?real_stream--rtp-caching={self.rtp_caching}'
    #     )

    @classmethod
    def from_toml(cls, tomlfile: Path) -> CMSConfig:
        """Load configuration from a TOML file."""
        with open(tomlfile, 'rb') as f:
            data = tomllib.load(f)

        if 'default_quality' in data:
            data['default_quality'] = StreamQuality[data['default_quality']]

        if 'channels' in data:
            data['channels'] = {int(k): v for k, v in data['channels'].items()}

        data['config_toml'] = tomlfile

        return cls(**data)


#
# def default_config() -> CMSConfig:
#     return CMSConfig.from_toml(Path(r'D:\prdev\tools\cms\default_conf.toml'))


_PROJECT_ROOT = Path(__file__).parent.parent.parent  # src/cms -> src -> project root


def setup_logging(debug: bool = True) -> None:
    """Configure the root *cms* logger.

    When *debug* is ``True`` the level is set to ``DEBUG`` and a simple
    timestamped handler is attached (idempotent — safe to call multiple times).
    When *debug* is ``False`` logging is effectively silenced at ``WARNING``
    level so nothing appears in normal use.
    """
    logger = logging.getLogger('cms')
    if logger.handlers:
        # Already configured — just update the level.
        logger.setLevel(logging.DEBUG if debug else logging.WARNING)
        return

    level = logging.DEBUG if debug else logging.WARNING
    logger.setLevel(level)

    handler = logging.StreamHandler()
    handler.setLevel(level)
    fmt = logging.Formatter(
        '[%(asctime)s] %(levelname)-8s %(name)s %(message)s "%(pathname)s:%(lineno)d"',
        datefmt='%H:%M:%S',
    )
    handler.setFormatter(fmt)
    logger.addHandler(handler)


def default_config() -> CMSConfig:
    return CMSConfig.from_toml(_PROJECT_ROOT / 'default_conf.toml')
