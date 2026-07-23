"""Runtime configuration, resolved from environment variables with sensible defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Final

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
    rtsp_user: str = field(default_factory=lambda: os.getenv('RTSP_USER', ''))
    rtsp_pass: str = field(default_factory=lambda: os.getenv('RTSP_PASS', ''))
    rtsp_host: str = field(default_factory=lambda: os.getenv('RTSP_HOST', '192.168.1.8'))
    rtsp_port: int = 554

    # VLC
    vlc_path: str = field(
        default_factory=lambda: os.getenv(
            'VLC_PATH', r'C:\Program Files (x86)\VideoLAN\VLC\vlc.exe'
        )
    )

    # Stream tunables
    rtp_caching: int = 100
    default_stream: int = 0  # 0 = main / high-quality,  1 = sub / low-quality
    default_quality: StreamQuality = StreamQuality.HIGH
    default_codec: str = 'H264'

    # ------------------------------------------------------------------ #
    def build_url(
        self,
        channel: int,
        stream: int | None = None,
        codec: str | None = None,
    ) -> str:
        """Return a fully-qualified RTSP URL for *channel*.

        Uses the DVR/NVR proprietary query-string credential format
        (``/user=…&password=…&channel=…``) that matches the original bat
        script.  Embedding credentials in the ``user:pass@host`` part of the
        URL causes VLC to trigger an RTSP digest-auth dialog instead.

        Args:
            channel: Camera channel number (1-based).
            stream:  0 = main (high quality), 1 = sub (low quality).
                     Falls back to :attr:`default_stream` when *None*.
            codec:   Unused in this URL scheme but kept for API consistency.
        """
        # s = self.default_stream if stream is None else stream
        s = self.default_quality.value if stream is None else stream
        return (
            f'rtsp://{self.rtsp_host}:{self.rtsp_port}'
            f'/user={self.rtsp_user}&password={self.rtsp_pass}'
            f'&channel={channel}&stream={s}.sdp'
            f'?real_stream--rtp-caching={self.rtp_caching}'
        )


CHANNEL_GROUPS: Final[dict[str, list[int]]] = {
    'doors': [2, 6],
    'front': [1, 2, 6, 8],
    'main': [1],
    'office': [4, 10],
    'all': list(range(1, 17)),
}
DEFAULT_GROUP: Final[str] = 'doors'
MAX_CHANNEL: Final[int] = 16
