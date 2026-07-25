"""CMS — Camera Management System.

Public API::

    from cms import CMSPlayer, CMSConfig, CHANNEL_GROUPS, StreamQuality

    player = CMSPlayer()
    player.open_group("doors")
    player.upgrade_quality()
    player.reload()
    player.close_all()
"""

from .config import CMSConfig
from .channels import StreamQuality
from .player import CMSPlayer

__all__ = ['CMSConfig', 'CMSPlayer', 'StreamQuality']
__version__ = '0.2.0'
