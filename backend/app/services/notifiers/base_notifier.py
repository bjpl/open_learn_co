"""
Base Notifier Abstract Class
All notification delivery methods inherit from this base
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User


class BaseNotifier(ABC):
    """Abstract base class for all notification delivery methods"""

    def __init__(self, db: AsyncSession):
        self.db = db

    @abstractmethod
    async def send(
        self,
        user: User,
        subject: str,
        content: Dict[str, Any],
        template: Optional[str] = None,
        **kwargs
    ) -> bool:
        """
        Send a notification to a user

        Args:
            user: User to send notification to
            subject: Notification subject/title
            content: Notification content data
            template: Optional template name
            **kwargs: Additional notifier-specific parameters

        Returns:
            bool: True if sent successfully, False otherwise
        """
        pass

    @abstractmethod
    async def send_bulk(
        self,
        users: List[User],
        subject: str,
        content: Dict[str, Any],
        template: Optional[str] = None,
        **kwargs
    ) -> Dict[int, bool]:
        """
        Send notification to multiple users

        Args:
            users: List of users to send to
            subject: Notification subject/title
            content: Notification content data
            template: Optional template name
            **kwargs: Additional notifier-specific parameters

        Returns:
            Dict[int, bool]: Mapping of user_id to success status
        """
        pass

    async def should_send(self, user: User) -> bool:
        """
        Check if notification should be sent to this user
        Override in subclasses for specific checks

        Args:
            user: User to check

        Returns:
            bool: True if notification should be sent
        """
        return True

    def format_content(
        self,
        template: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Format notification content with template and context

        Args:
            template: Template string
            context: Template context variables

        Returns:
            str: Formatted content
        """
        try:
            return template.format(**context)
        except KeyError as e:
            raise ValueError(f"Missing template variable: {e}")
