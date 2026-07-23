"""Channel groups and stream quality definitions."""

from __future__ import annotations

from enum import IntEnum


class StreamQuality(IntEnum):
    """VLC sub-stream index.

    HIGH (0) = main stream — full resolution, higher bandwidth.
    LOW  (1) = sub  stream — reduced resolution, lower bandwidth.
    """

    HIGH = 0
    LOW = 1

    def label(self) -> str:
        return 'HIGH' if self == StreamQuality.HIGH else 'LOW'

    def toggled(self) -> 'StreamQuality':
        return StreamQuality.LOW if self == StreamQuality.HIGH else StreamQuality.HIGH


# Named channel groups ————————————————————————————————————————————————————

