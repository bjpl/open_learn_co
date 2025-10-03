"""
Tests for Notification Service
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.notification_service import NotificationService
from app.database.notification_models import (
    Notification, NotificationPreference,
    NotificationType, NotificationCategory, NotificationPriority
)
from app.database.models import User


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """Create a test user"""
    user = User(
        email="test@example.com",
        username="testuser",
        password_hash="hashed_password",
        full_name="Test User",
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def notification_service(db_session: AsyncSession):
    """Create notification service instance"""
    return NotificationService(db_session)


@pytest.mark.asyncio
async def test_create_notification(notification_service, test_user):
    """Test creating a notification"""

    notification = await notification_service.create_notification(
        user_id=test_user.id,
        category=NotificationCategory.NEW_CONTENT,
        title="Test Notification",
        message="This is a test notification",
        type=NotificationType.INFO,
        priority=NotificationPriority.MEDIUM
    )

    assert notification is not None
    assert notification.user_id == test_user.id
    assert notification.title == "Test Notification"
    assert notification.message == "This is a test notification"
    assert notification.read == False
    assert notification.category == NotificationCategory.NEW_CONTENT


@pytest.mark.asyncio
async def test_get_user_notifications(notification_service, test_user):
    """Test getting user notifications"""

    # Create test notifications
    for i in range(5):
        await notification_service.create_notification(
            user_id=test_user.id,
            category=NotificationCategory.NEW_CONTENT,
            title=f"Test {i}",
            message=f"Message {i}",
            type=NotificationType.INFO
        )

    # Get notifications
    notifications, total = await notification_service.get_user_notifications(
        user_id=test_user.id,
        limit=10,
        offset=0
    )

    assert total == 5
    assert len(notifications) == 5


@pytest.mark.asyncio
async def test_get_unread_count(notification_service, test_user):
    """Test getting unread notification count"""

    # Create notifications
    for i in range(3):
        await notification_service.create_notification(
            user_id=test_user.id,
            category=NotificationCategory.NEW_CONTENT,
            title=f"Test {i}",
            message=f"Message {i}"
        )

    # Get unread count
    count = await notification_service.get_unread_count(test_user.id)
    assert count == 3


@pytest.mark.asyncio
async def test_mark_as_read(notification_service, test_user):
    """Test marking notification as read"""

    # Create notification
    notification = await notification_service.create_notification(
        user_id=test_user.id,
        category=NotificationCategory.NEW_CONTENT,
        title="Test",
        message="Test message"
    )

    # Mark as read
    success = await notification_service.mark_as_read(notification.id, test_user.id)
    assert success == True

    # Verify it's read
    count = await notification_service.get_unread_count(test_user.id)
    assert count == 0


@pytest.mark.asyncio
async def test_mark_all_as_read(notification_service, test_user):
    """Test marking all notifications as read"""

    # Create notifications
    for i in range(5):
        await notification_service.create_notification(
            user_id=test_user.id,
            category=NotificationCategory.NEW_CONTENT,
            title=f"Test {i}",
            message=f"Message {i}"
        )

    # Mark all as read
    count = await notification_service.mark_all_as_read(test_user.id)
    assert count == 5

    # Verify all are read
    unread = await notification_service.get_unread_count(test_user.id)
    assert unread == 0


@pytest.mark.asyncio
async def test_delete_notification(notification_service, test_user):
    """Test deleting a notification"""

    # Create notification
    notification = await notification_service.create_notification(
        user_id=test_user.id,
        category=NotificationCategory.NEW_CONTENT,
        title="Test",
        message="Test message"
    )

    # Delete it
    success = await notification_service.delete_notification(notification.id, test_user.id)
    assert success == True

    # Verify it's gone
    notifications, total = await notification_service.get_user_notifications(
        user_id=test_user.id
    )
    assert total == 0


@pytest.mark.asyncio
async def test_notification_preferences(notification_service, test_user):
    """Test notification preferences"""

    # Create preferences
    prefs = await notification_service.create_or_update_preferences(
        user_id=test_user.id,
        email_digest_enabled=True,
        email_digest_time="09:00",
        in_app_notifications_enabled=True
    )

    assert prefs.user_id == test_user.id
    assert prefs.email_digest_enabled == True
    assert prefs.email_digest_time == "09:00"

    # Update preferences
    updated = await notification_service.create_or_update_preferences(
        user_id=test_user.id,
        email_digest_enabled=False
    )

    assert updated.email_digest_enabled == False
    assert updated.email_digest_time == "09:00"  # Unchanged


@pytest.mark.asyncio
async def test_rate_limiting(notification_service, test_user):
    """Test notification rate limiting"""

    # Set low rate limit
    await notification_service.create_or_update_preferences(
        user_id=test_user.id,
        max_in_app_per_hour=2
    )

    # Create notifications up to limit
    for i in range(2):
        notification = await notification_service.create_notification(
            user_id=test_user.id,
            category=NotificationCategory.NEW_CONTENT,
            title=f"Test {i}",
            message=f"Message {i}"
        )
        assert notification is not None

    # Next one should be blocked by rate limit
    notification = await notification_service.create_notification(
        user_id=test_user.id,
        category=NotificationCategory.NEW_CONTENT,
        title="Should be blocked",
        message="Rate limited"
    )
    assert notification is None


@pytest.mark.asyncio
async def test_cleanup_old_notifications(notification_service, test_user):
    """Test cleaning up old notifications"""

    # Create old notification
    old_notification = Notification(
        user_id=test_user.id,
        category=NotificationCategory.NEW_CONTENT,
        title="Old",
        message="Old notification",
        created_at=datetime.utcnow() - timedelta(days=35)
    )
    notification_service.db.add(old_notification)
    await notification_service.db.commit()

    # Create recent notification
    await notification_service.create_notification(
        user_id=test_user.id,
        category=NotificationCategory.NEW_CONTENT,
        title="Recent",
        message="Recent notification"
    )

    # Cleanup (30 days retention)
    deleted = await notification_service.cleanup_old_notifications(days=30)
    assert deleted >= 1

    # Verify recent one still exists
    notifications, total = await notification_service.get_user_notifications(
        user_id=test_user.id
    )
    assert total >= 1


@pytest.mark.asyncio
async def test_category_filtering(notification_service, test_user):
    """Test filtering notifications by category"""

    # Create different categories
    await notification_service.create_notification(
        user_id=test_user.id,
        category=NotificationCategory.NEW_CONTENT,
        title="Content",
        message="New content"
    )

    await notification_service.create_notification(
        user_id=test_user.id,
        category=NotificationCategory.VOCABULARY,
        title="Vocab",
        message="Vocabulary reminder"
    )

    # Filter by category
    notifications, total = await notification_service.get_user_notifications(
        user_id=test_user.id,
        category=NotificationCategory.NEW_CONTENT
    )

    assert total == 1
    assert notifications[0].category == NotificationCategory.NEW_CONTENT
