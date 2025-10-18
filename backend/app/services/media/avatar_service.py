"""
Avatar Upload and Management Service
Handles avatar uploads with security validation and storage
"""

import os
import shutil
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime
import logging

from ...utils.security.image_validator import (
    ImageValidator,
    ImageValidationError,
    default_validator
)

logger = logging.getLogger(__name__)


class AvatarStorageError(Exception):
    """Custom exception for avatar storage errors"""
    pass


class AvatarService:
    """
    Manages avatar uploads and storage

    Features:
    - Secure file validation
    - Local file storage (cloud-ready)
    - Old avatar cleanup
    - URL generation
    """

    def __init__(
        self,
        storage_path: str = "uploads/avatars",
        base_url: str = "/api/avatars",
        validator: Optional[ImageValidator] = None
    ):
        """
        Initialize avatar service

        Args:
            storage_path: Local path for storing avatars
            base_url: Base URL for serving avatars
            validator: Image validator instance (uses default if None)
        """
        self.storage_path = Path(storage_path)
        self.base_url = base_url.rstrip('/')
        self.validator = validator or default_validator

        # Ensure storage directory exists
        self.storage_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"AvatarService initialized: storage={self.storage_path}")

    def upload_avatar(
        self,
        user_id: int,
        file_data: bytes,
        filename: str,
        old_avatar_url: Optional[str] = None
    ) -> Tuple[str, dict]:
        """
        Upload and process avatar image

        Args:
            user_id: User ID
            file_data: Raw file bytes
            filename: Original filename
            old_avatar_url: Previous avatar URL to delete (if any)

        Returns:
            Tuple of (avatar_url, metadata)

        Raises:
            ImageValidationError: If validation fails
            AvatarStorageError: If storage fails
        """
        try:
            logger.info(f"Processing avatar upload for user {user_id}")

            # 1. Validate and process image
            clean_data, format, metadata = self.validator.validate_and_process(
                file_data,
                filename
            )

            # 2. Generate safe filename
            safe_filename = self.validator.sanitize_filename(filename, user_id)

            # 3. Save to storage
            file_path = self.storage_path / safe_filename

            try:
                with open(file_path, 'wb') as f:
                    f.write(clean_data)
                logger.info(f"Avatar saved: {file_path}")
            except Exception as e:
                logger.error(f"Failed to save avatar: {e}")
                raise AvatarStorageError(f"Failed to save avatar: {str(e)}")

            # 4. Generate URL
            avatar_url = f"{self.base_url}/{safe_filename}"

            # 5. Clean up old avatar if exists
            if old_avatar_url:
                self.delete_avatar(old_avatar_url)

            # 6. Add storage metadata
            metadata.update({
                'uploaded_at': datetime.utcnow().isoformat(),
                'user_id': user_id,
                'filename': safe_filename,
                'storage_path': str(file_path),
                'url': avatar_url
            })

            logger.info(f"Avatar upload complete for user {user_id}: {avatar_url}")

            return avatar_url, metadata

        except ImageValidationError:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            logger.error(f"Avatar upload failed for user {user_id}: {e}")
            raise AvatarStorageError(f"Avatar upload failed: {str(e)}")

    def delete_avatar(self, avatar_url: str) -> bool:
        """
        Delete avatar file

        Args:
            avatar_url: Avatar URL to delete

        Returns:
            True if deleted, False if not found
        """
        try:
            # Extract filename from URL
            filename = avatar_url.split('/')[-1]
            file_path = self.storage_path / filename

            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted avatar: {file_path}")
                return True
            else:
                logger.warning(f"Avatar not found for deletion: {file_path}")
                return False

        except Exception as e:
            logger.error(f"Failed to delete avatar {avatar_url}: {e}")
            return False

    def get_avatar_path(self, avatar_url: str) -> Optional[Path]:
        """
        Get local file path for avatar URL

        Args:
            avatar_url: Avatar URL

        Returns:
            Path object if exists, None otherwise
        """
        try:
            filename = avatar_url.split('/')[-1]
            file_path = self.storage_path / filename

            if file_path.exists():
                return file_path
            return None

        except Exception as e:
            logger.error(f"Failed to get avatar path for {avatar_url}: {e}")
            return None

    def cleanup_orphaned_avatars(self, active_avatar_urls: list[str]) -> int:
        """
        Clean up avatars that are no longer referenced

        Args:
            active_avatar_urls: List of currently active avatar URLs

        Returns:
            Number of files deleted
        """
        try:
            # Extract active filenames
            active_files = {url.split('/')[-1] for url in active_avatar_urls}

            # Get all files in storage
            all_files = set(f.name for f in self.storage_path.iterdir() if f.is_file())

            # Find orphaned files
            orphaned = all_files - active_files

            # Delete orphaned files
            deleted_count = 0
            for filename in orphaned:
                file_path = self.storage_path / filename
                try:
                    file_path.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted orphaned avatar: {filename}")
                except Exception as e:
                    logger.error(f"Failed to delete orphaned avatar {filename}: {e}")

            logger.info(f"Cleanup complete: {deleted_count} orphaned avatars deleted")
            return deleted_count

        except Exception as e:
            logger.error(f"Avatar cleanup failed: {e}")
            return 0


# Global service instance
avatar_service = AvatarService()
