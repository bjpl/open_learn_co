"""
Notification API Endpoints
RESTful API for managing user notifications
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.services.notification_service import NotificationService
from app.database.notification_models import NotificationCategory, NotificationType, NotificationPriority
from app.api.auth import get_current_user
from app.database.models import User


router = APIRouter()


# Pydantic Models

class NotificationResponse(BaseModel):
    """Notification response model"""
    id: int
    type: str
    category: str
    priority: str
    title: str
    message: str
    action_url: Optional[str] = None
    action_label: Optional[str] = None
    metadata: Optional[dict] = None
    read: bool
    read_at: Optional[str] = None
    created_at: str
    expires_at: Optional[str] = None


class NotificationListResponse(BaseModel):
    """Paginated notification list response"""
    items: List[NotificationResponse]
    total: int
    unread: int
    page: int
    pages: int
    per_page: int


class UnreadCountResponse(BaseModel):
    """Unread notification count response"""
    count: int
    latest: Optional[NotificationResponse] = None


class NotificationPreferenceUpdate(BaseModel):
    """Update notification preferences"""
    email_digest_enabled: Optional[bool] = None
    email_digest_time: Optional[str] = Field(None, pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    email_weekly_enabled: Optional[bool] = None
    email_alerts_enabled: Optional[bool] = None
    email_vocabulary_enabled: Optional[bool] = None
    in_app_notifications_enabled: Optional[bool] = None
    notification_categories: Optional[List[str]] = None
    quiet_hours_start: Optional[str] = Field(None, pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    quiet_hours_end: Optional[str] = Field(None, pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    timezone: Optional[str] = None


class NotificationPreferenceResponse(BaseModel):
    """Notification preferences response"""
    user_id: int
    email_digest_enabled: bool
    email_digest_time: str
    email_weekly_enabled: bool
    email_alerts_enabled: bool
    email_vocabulary_enabled: bool
    in_app_notifications_enabled: bool
    notification_categories: List[str]
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    max_emails_per_day: int
    max_in_app_per_hour: int
    timezone: str


# Endpoints

@router.get("/notifications", response_model=NotificationListResponse)
async def get_notifications(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    unread_only: bool = Query(False, description="Show only unread notifications"),
    category: Optional[str] = Query(None, description="Filter by category"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's notifications with pagination

    - **page**: Page number (starts at 1)
    - **per_page**: Items per page (max 100)
    - **unread_only**: Filter to unread notifications only
    - **category**: Filter by notification category
    """

    service = NotificationService(db)

    # Parse category if provided
    cat_filter = None
    if category:
        try:
            cat_filter = NotificationCategory[category.upper()]
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category: {category}"
            )

    # Get notifications
    offset = (page - 1) * per_page
    notifications, total = await service.get_user_notifications(
        user_id=current_user.id,
        unread_only=unread_only,
        category=cat_filter,
        limit=per_page,
        offset=offset
    )

    # Get unread count
    unread_count = await service.get_unread_count(current_user.id)

    # Calculate pages
    pages = (total + per_page - 1) // per_page

    return NotificationListResponse(
        items=[NotificationResponse(**n.to_dict()) for n in notifications],
        total=total,
        unread=unread_count,
        page=page,
        pages=pages,
        per_page=per_page
    )


@router.get("/notifications/unread", response_model=UnreadCountResponse)
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get count of unread notifications and the latest notification
    """

    service = NotificationService(db)

    # Get unread count
    count = await service.get_unread_count(current_user.id)

    # Get latest notification
    latest = None
    if count > 0:
        notifications, _ = await service.get_user_notifications(
            user_id=current_user.id,
            unread_only=True,
            limit=1,
            offset=0
        )
        if notifications:
            latest = NotificationResponse(**notifications[0].to_dict())

    return UnreadCountResponse(count=count, latest=latest)


@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark a specific notification as read
    """

    service = NotificationService(db)

    success = await service.mark_as_read(notification_id, current_user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )

    return {"success": True, "message": "Notification marked as read"}


@router.put("/notifications/read-all")
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark all notifications as read for the current user
    """

    service = NotificationService(db)

    count = await service.mark_all_as_read(current_user.id)

    return {
        "success": True,
        "message": f"Marked {count} notifications as read",
        "count": count
    }


@router.delete("/notifications/{notification_id}")
async def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a specific notification
    """

    service = NotificationService(db)

    success = await service.delete_notification(notification_id, current_user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )

    return {"success": True, "message": "Notification deleted"}


@router.delete("/notifications/clear")
async def clear_read_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Clear all read notifications for the current user
    """

    service = NotificationService(db)

    count = await service.clear_read_notifications(current_user.id)

    return {
        "success": True,
        "message": f"Cleared {count} read notifications",
        "count": count
    }


# Notification Preferences

@router.get("/notifications/preferences", response_model=NotificationPreferenceResponse)
async def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get notification preferences for the current user
    """

    service = NotificationService(db)

    prefs = await service.get_user_preferences(current_user.id)

    if not prefs:
        # Create default preferences
        prefs = await service.create_or_update_preferences(current_user.id)

    return NotificationPreferenceResponse(**prefs.to_dict())


@router.put("/notifications/preferences", response_model=NotificationPreferenceResponse)
async def update_notification_preferences(
    preferences: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update notification preferences for the current user
    """

    service = NotificationService(db)

    # Filter out None values
    update_data = {k: v for k, v in preferences.dict().items() if v is not None}

    prefs = await service.create_or_update_preferences(
        current_user.id,
        **update_data
    )

    return NotificationPreferenceResponse(**prefs.to_dict())
