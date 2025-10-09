"""
Notification Service
Core notification logic for creating, managing, and delivering notifications
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.notification_models import (
    Notification, NotificationPreference, EmailLog,
    NotificationType, NotificationCategory, NotificationPriority
)
from app.database.models import User


class NotificationService:
    """Service for managing notifications"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_notification(
        self,
        user_id: int,
        category: NotificationCategory,
        title: str,
        message: str,
        type: NotificationType = NotificationType.INFO,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        action_url: Optional[str] = None,
        action_label: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        expires_in_days: Optional[int] = None
    ) -> Notification:
        """Create a new notification for a user"""

        # Check user preferences
        prefs = await self.get_user_preferences(user_id)
        if prefs and not prefs.in_app_notifications_enabled:
            return None

        # Check category preferences
        if prefs and prefs.notification_categories:
            if category.value not in prefs.notification_categories:
                return None

        # Check rate limits
        if prefs and not await self._check_rate_limit(user_id, prefs.max_in_app_per_hour):
            return None

        # Create notification
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        notification = Notification(
            user_id=user_id,
            type=type,
            category=category,
            priority=priority,
            title=title,
            message=message,
            action_url=action_url,
            action_label=action_label,
            metadata=metadata,
            expires_at=expires_at
        )

        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)

        return notification

    async def get_user_notifications(
        self,
        user_id: int,
        unread_only: bool = False,
        category: Optional[NotificationCategory] = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[Notification], int]:
        """Get notifications for a user with pagination"""

        # Build query
        query = select(Notification).where(Notification.user_id == user_id)

        # Apply filters
        if unread_only:
            query = query.where(Notification.read == False)

        if category:
            query = query.where(Notification.category == category)

        # Filter out expired notifications
        query = query.where(
            or_(
                Notification.expires_at.is_(None),
                Notification.expires_at > datetime.utcnow()
            )
        )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar()

        # Apply ordering and pagination
        query = query.order_by(
            Notification.priority.desc(),
            Notification.created_at.desc()
        )
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        notifications = result.scalars().all()

        return list(notifications), total

    async def get_unread_count(self, user_id: int) -> int:
        """Get count of unread notifications for a user"""
        query = select(func.count()).where(
            and_(
                Notification.user_id == user_id,
                Notification.read == False,
                or_(
                    Notification.expires_at.is_(None),
                    Notification.expires_at > datetime.utcnow()
                )
            )
        )
        result = await self.db.execute(query)
        return result.scalar()

    async def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """Mark a notification as read"""
        stmt = (
            update(Notification)
            .where(
                and_(
                    Notification.id == notification_id,
                    Notification.user_id == user_id
                )
            )
            .values(read=True, read_at=datetime.utcnow())
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0

    async def mark_all_as_read(self, user_id: int) -> int:
        """Mark all notifications as read for a user"""
        stmt = (
            update(Notification)
            .where(
                and_(
                    Notification.user_id == user_id,
                    Notification.read == False
                )
            )
            .values(read=True, read_at=datetime.utcnow())
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount

    async def delete_notification(self, notification_id: int, user_id: int) -> bool:
        """Delete a notification"""
        stmt = delete(Notification).where(
            and_(
                Notification.id == notification_id,
                Notification.user_id == user_id
            )
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0

    async def clear_read_notifications(self, user_id: int) -> int:
        """Clear all read notifications for a user"""
        stmt = delete(Notification).where(
            and_(
                Notification.user_id == user_id,
                Notification.read == True
            )
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount

    async def cleanup_old_notifications(self, days: int = 30) -> int:
        """Delete notifications older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        stmt = delete(Notification).where(
            Notification.created_at < cutoff_date
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount

    async def cleanup_expired_notifications(self) -> int:
        """Delete expired notifications"""
        stmt = delete(Notification).where(
            and_(
                Notification.expires_at.isnot(None),
                Notification.expires_at < datetime.utcnow()
            )
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount

    # Notification Preferences

    async def get_user_preferences(self, user_id: int) -> Optional[NotificationPreference]:
        """Get notification preferences for a user"""
        query = select(NotificationPreference).where(
            NotificationPreference.user_id == user_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_or_update_preferences(
        self,
        user_id: int,
        **kwargs
    ) -> NotificationPreference:
        """Create or update notification preferences"""

        # Check if preferences exist
        prefs = await self.get_user_preferences(user_id)

        if prefs:
            # Update existing
            for key, value in kwargs.items():
                if hasattr(prefs, key):
                    setattr(prefs, key, value)
            prefs.updated_at = datetime.utcnow()
        else:
            # Create new
            prefs = NotificationPreference(user_id=user_id, **kwargs)
            self.db.add(prefs)

        await self.db.commit()
        await self.db.refresh(prefs)
        return prefs

    # Email Logging

    async def log_email(
        self,
        user_id: int,
        email_type: str,
        recipient: str,
        subject: str,
        sent: bool = False,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EmailLog:
        """Log an email send attempt"""

        email_log = EmailLog(
            user_id=user_id,
            email_type=email_type,
            recipient=recipient,
            subject=subject,
            sent=sent,
            sent_at=datetime.utcnow() if sent else None,
            error_message=error_message,
            metadata=metadata
        )

        self.db.add(email_log)
        await self.db.commit()
        await self.db.refresh(email_log)

        return email_log

    async def get_email_stats(
        self,
        user_id: Optional[int] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get email sending statistics"""

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        query = select(EmailLog).where(EmailLog.created_at >= cutoff_date)
        if user_id:
            query = query.where(EmailLog.user_id == user_id)

        result = await self.db.execute(query)
        logs = result.scalars().all()

        total = len(logs)
        sent = sum(1 for log in logs if log.sent)
        failed = total - sent
        opened = sum(1 for log in logs if log.opened)
        clicked = sum(1 for log in logs if log.clicked)

        return {
            "total": total,
            "sent": sent,
            "failed": failed,
            "open_rate": (opened / sent * 100) if sent > 0 else 0,
            "click_rate": (clicked / sent * 100) if sent > 0 else 0,
        }

    # Helper Methods

    async def _check_rate_limit(self, user_id: int, max_per_hour: int) -> bool:
        """Check if user has exceeded notification rate limit"""

        one_hour_ago = datetime.utcnow() - timedelta(hours=1)

        query = select(func.count()).where(
            and_(
                Notification.user_id == user_id,
                Notification.created_at >= one_hour_ago
            )
        )

        result = await self.db.execute(query)
        count = result.scalar()

        return count < max_per_hour

    async def _check_quiet_hours(self, user_id: int) -> bool:
        """Check if current time is within user's quiet hours (timezone-aware)"""
        from app.utils.timezone_utils import is_in_quiet_hours

        prefs = await self.get_user_preferences(user_id)
        if not prefs or not prefs.quiet_hours_start or not prefs.quiet_hours_end:
            return False

        # Get user's timezone
        user_query = select(User).where(User.id == user_id)
        result = await self.db.execute(user_query)
        user = result.scalar_one_or_none()

        if not user:
            return False

        # Check if currently in quiet hours (timezone-aware)
        return is_in_quiet_hours(
            quiet_start=prefs.quiet_hours_start,
            quiet_end=prefs.quiet_hours_end,
            user_timezone=user.timezone
        )
