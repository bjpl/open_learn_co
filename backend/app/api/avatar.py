"""
Avatar Upload API
Production-grade avatar management with security validation
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import logging

from ..core.security import get_current_active_user
from ..database.connection import get_db
from ..database.models import User
from ..services.media.avatar_service import (
    avatar_service,
    AvatarStorageError
)
from ..utils.security.image_validator import ImageValidationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/avatars", tags=["avatars"])


# ============================================================================
# Pydantic Models
# ============================================================================

class AvatarUploadResponse(BaseModel):
    """Avatar upload response model"""
    avatar_url: str
    metadata: dict
    message: str = "Avatar uploaded successfully"

    class Config:
        json_schema_extra = {
            "example": {
                "avatar_url": "/api/avatars/avatar_123_1234567890_a1b2c3d4.jpg",
                "metadata": {
                    "width": 800,
                    "height": 800,
                    "processed_format": "JPEG",
                    "original_size_bytes": 524288,
                    "processed_size_bytes": 245760
                },
                "message": "Avatar uploaded successfully"
            }
        }


class AvatarDeleteResponse(BaseModel):
    """Avatar delete response model"""
    message: str
    deleted: bool


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/upload", response_model=AvatarUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_avatar(
    file: UploadFile = File(..., description="Avatar image file"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload user avatar image

    Security features:
    - File type validation (magic bytes, not just extension)
    - Size limits (5MB max by default)
    - EXIF data stripping (prevents privacy leaks)
    - Image reprocessing (prevents exploits)
    - Dimension validation
    - Filename sanitization (prevents path traversal)

    **Allowed formats**: JPEG, PNG, GIF, WebP

    **Max size**: 5MB

    **Recommended**: Square images, 200x200 to 1000x1000 pixels

    Returns:
    - **avatar_url**: URL to access the uploaded avatar
    - **metadata**: Image processing metadata (dimensions, size, etc.)
    """
    try:
        logger.info(f"Avatar upload request from user {current_user.id}")

        # Read file data
        file_data = await file.read()

        if not file_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file data received"
            )

        # Get original filename
        filename = file.filename or "avatar.jpg"

        # Get old avatar URL for cleanup
        old_avatar_url = current_user.avatar_url

        # Upload and process avatar
        try:
            avatar_url, metadata = avatar_service.upload_avatar(
                user_id=current_user.id,
                file_data=file_data,
                filename=filename,
                old_avatar_url=old_avatar_url
            )
        except ImageValidationError as e:
            logger.warning(f"Avatar validation failed for user {current_user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except AvatarStorageError as e:
            logger.error(f"Avatar storage failed for user {current_user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save avatar. Please try again."
            )

        # Update user record
        current_user.avatar_url = avatar_url
        current_user.avatar_metadata = metadata

        db.commit()
        db.refresh(current_user)

        logger.info(f"Avatar updated for user {current_user.id}: {avatar_url}")

        return AvatarUploadResponse(
            avatar_url=avatar_url,
            metadata=metadata
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error during avatar upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Avatar upload failed. Please try again."
        )


@router.delete("/", response_model=AvatarDeleteResponse)
async def delete_avatar(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete current user's avatar

    Removes the avatar file and updates the user record.
    """
    try:
        if not current_user.avatar_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No avatar to delete"
            )

        # Delete file
        deleted = avatar_service.delete_avatar(current_user.avatar_url)

        # Update user record
        current_user.avatar_url = None
        current_user.avatar_metadata = None

        db.commit()

        logger.info(f"Avatar deleted for user {current_user.id}")

        return AvatarDeleteResponse(
            message="Avatar deleted successfully",
            deleted=deleted
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete avatar for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete avatar. Please try again."
        )


@router.get("/{filename}")
async def get_avatar(filename: str):
    """
    Serve avatar file

    Returns the avatar image file for the given filename.

    **Note**: This is a simple file server. In production, consider:
    - Using a CDN for better performance
    - Adding caching headers
    - Using cloud storage (S3, GCS, etc.)
    """
    try:
        # Validate filename (prevent path traversal)
        if '/' in filename or '\\' in filename or '..' in filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename"
            )

        # Get file path
        file_path = avatar_service.get_avatar_path(f"/api/avatars/{filename}")

        if not file_path or not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Avatar not found"
            )

        # Determine media type from extension
        ext = file_path.suffix.lower()
        media_type_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        media_type = media_type_map.get(ext, 'application/octet-stream')

        # Return file with caching headers
        return FileResponse(
            file_path,
            media_type=media_type,
            headers={
                'Cache-Control': 'public, max-age=86400',  # Cache for 24 hours
                'ETag': f'"{file_path.stat().st_mtime}"'  # Simple ETag
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to serve avatar {filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve avatar"
        )


@router.get("/health", include_in_schema=False)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "avatar_upload",
        "storage_path": str(avatar_service.storage_path)
    }
