"""Media services package"""

from .avatar_service import (
    AvatarService,
    AvatarStorageError,
    avatar_service
)

__all__ = [
    'AvatarService',
    'AvatarStorageError',
    'avatar_service'
]
