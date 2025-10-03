"""
In-App Notifier
Creates in-app notifications stored in database
"""

from typing import Dict, Any, Optional, List
import logging

from app.services.notifiers.base_notifier import BaseNotifier
from app.services.notification_service import NotificationService
from app.database.notification_models import NotificationType, NotificationCategory, NotificationPriority
from app.database.models import User


logger = logging.getLogger(__name__)


class InAppNotifier(BaseNotifier):
    """In-app notification delivery"""

    async def send(
        self,
        user: User,
        subject: str,
        content: Dict[str, Any],
        template: Optional[str] = None,
        **kwargs
    ) -> bool:
        """Create an in-app notification for a user"""

        service = NotificationService(self.db)

        # Check if in-app notifications are enabled
        if not await self.should_send(user):
            logger.info(f"In-app notifications disabled for user {user.id}")
            return False

        try:
            # Extract notification parameters
            category = kwargs.get("category", NotificationCategory.SYSTEM)
            if isinstance(category, str):
                category = NotificationCategory[category.upper()]

            notification_type = kwargs.get("type", NotificationType.INFO)
            if isinstance(notification_type, str):
                notification_type = NotificationType[notification_type.upper()]

            priority = kwargs.get("priority", NotificationPriority.MEDIUM)
            if isinstance(priority, str):
                priority = NotificationPriority[priority.upper()]

            # Create notification
            notification = await service.create_notification(
                user_id=user.id,
                category=category,
                title=subject,
                message=content.get("message", ""),
                type=notification_type,
                priority=priority,
                action_url=content.get("action_url"),
                action_label=content.get("action_label"),
                metadata=content.get("metadata"),
                expires_in_days=kwargs.get("expires_in_days")
            )

            if notification:
                logger.info(f"In-app notification created for user {user.id}: {subject}")
                return True
            else:
                logger.warning(f"In-app notification not created (preferences or rate limit)")
                return False

        except Exception as e:
            logger.error(f"Failed to create in-app notification for user {user.id}: {e}")
            return False

    async def send_bulk(
        self,
        users: List[User],
        subject: str,
        content: Dict[str, Any],
        template: Optional[str] = None,
        **kwargs
    ) -> Dict[int, bool]:
        """Create in-app notifications for multiple users"""

        results = {}

        for user in users:
            results[user.id] = await self.send(user, subject, content, template, **kwargs)

        return results

    async def should_send(self, user: User) -> bool:
        """Check if in-app notification should be created for this user"""

        service = NotificationService(self.db)
        prefs = await service.get_user_preferences(user.id)

        # Check if in-app notifications are enabled
        if prefs and not prefs.in_app_notifications_enabled:
            return False

        return True
