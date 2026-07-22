"""Channel groups and stream quality definitions."""
from __future__ import annotations

from enum import IntEnum
from typing import Final


class StreamQuality(IntEnum):
    """VLC sub-stream index.

    HIGH (0) = main stream — full resolution, higher bandwidth.
    LOW  (1) = sub  stream — reduced resolution, lower bandwidth.
    """

    HIGH = 0
    LOW = 1

    def label(self) -> str:
        return "HIGH" if self == StreamQuality.HIGH else "LOW"

    def toggled(self) -> "StreamQuality":
        return StreamQuality.LOW if self == StreamQuality.HIGH else StreamQuality.HIGH


# Named channel groups ————————————————————————————————————————————————————
CHANNEL_GROUPS: Final[dict[str, list[int]]] = {
    "doors":  [2, 6],
    "front":  [1, 2, 6, 8],
    "main":   [1],
    "office": [4, 10],
    "all":    list(range(1, 17)),
}

DEFAULT_GROUP: Final[str] = "doors"
MAX_CHANNEL: Final[int] = 16

