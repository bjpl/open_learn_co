"""
Notification Triggers
Event-based triggers for creating notifications
"""

from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.database.models import User, ScrapedContent, UserVocabulary
from app.database.notification_models import NotificationCategory, NotificationType, NotificationPriority
from app.services.notifiers.in_app_notifier import InAppNotifier
from app.services.notifiers.email_notifier import EmailNotifier


logger = logging.getLogger(__name__)


class NotificationTriggers:
    """Manages event-based notification triggers"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.in_app_notifier = InAppNotifier(db)
        self.email_notifier = EmailNotifier(db)

    async def trigger_new_content_alert(
        self,
        content_id: int,
        matching_users: Optional[List[int]] = None
    ):
        """
        Trigger notification for new content matching user interests

        Args:
            content_id: ID of the new content
            matching_users: Optional list of user IDs who should be notified
        """

        # Get content details
        query = select(ScrapedContent).where(ScrapedContent.id == content_id)
        result = await self.db.execute(query)
        content = result.scalar_one_or_none()

        if not content:
            logger.warning(f"Content {content_id} not found for notification")
            return

        # If no users specified, find users interested in this type of content
        if not matching_users:
            matching_users = await self._find_interested_users(content)

            if not matching_users:
                logger.debug(f"No users interested in content {content_id}")
                return

        # Get matching users
        users_query = select(User).where(User.id.in_(matching_users))
        result = await self.db.execute(users_query)
        users = result.scalars().all()

        # Send notifications
        for user in users:
            # Create in-app notification
            await self.in_app_notifier.send(
                user=user,
                subject="New Article Available",
                content={
                    "message": f"New article from {content.source}: {content.title[:100]}",
                    "action_url": f"/news/{content.id}",
                    "action_label": "Read Now",
                    "metadata": {"content_id": content.id}
                },
                category=NotificationCategory.NEW_CONTENT,
                type=NotificationType.INFO,
                priority=NotificationPriority.MEDIUM,
                expires_in_days=7
            )

    async def trigger_vocabulary_reminder(self, user_id: int):
        """
        Trigger vocabulary review reminder for a user

        Args:
            user_id: User ID to send reminder to
        """

        # Get user
        user_query = select(User).where(User.id == user_id)
        result = await self.db.execute(user_query)
        user = result.scalar_one_or_none()

        if not user:
            return

        # Get vocabulary due for review
        vocab_query = select(func.count()).where(
            and_(
                UserVocabulary.user_id == user_id,
                UserVocabulary.next_review <= datetime.utcnow(),
                UserVocabulary.mastery_level < 1.0
            )
        )

        result = await self.db.execute(vocab_query)
        vocab_count = result.scalar()

        if vocab_count == 0:
            return

        # Send in-app notification
        await self.in_app_notifier.send(
            user=user,
            subject="Time to Review Vocabulary",
            content={
                "message": f"You have {vocab_count} words ready for review",
                "action_url": "/vocabulary/review",
                "action_label": "Start Review",
                "metadata": {"vocab_count": vocab_count}
            },
            category=NotificationCategory.VOCABULARY,
            type=NotificationType.INFO,
            priority=NotificationPriority.MEDIUM,
            expires_in_days=1
        )

    async def trigger_achievement_notification(
        self,
        user_id: int,
        achievement_name: str,
        achievement_description: str
    ):
        """
        Trigger achievement unlock notification

        Args:
            user_id: User ID
            achievement_name: Name of the achievement
            achievement_description: Description of the achievement
        """

        # Get user
        user_query = select(User).where(User.id == user_id)
        result = await self.db.execute(user_query)
        user = result.scalar_one_or_none()

        if not user:
            return

        # Send in-app notification
        await self.in_app_notifier.send(
            user=user,
            subject=f"Achievement Unlocked: {achievement_name}",
            content={
                "message": achievement_description,
                "action_url": "/profile/achievements",
                "action_label": "View Achievements",
                "metadata": {"achievement": achievement_name}
            },
            category=NotificationCategory.ACHIEVEMENT,
            type=NotificationType.SUCCESS,
            priority=NotificationPriority.HIGH,
            expires_in_days=30
        )

    async def trigger_system_alert(
        self,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        user_ids: Optional[List[int]] = None
    ):
        """
        Trigger system-wide alert

        Args:
            message: Alert message
            priority: Alert priority
            user_ids: Optional list of specific user IDs (None = all users)
        """

        # Get users
        if user_ids:
            users_query = select(User).where(User.id.in_(user_ids))
        else:
            users_query = select(User).where(User.is_active == True)

        result = await self.db.execute(users_query)
        users = result.scalars().all()

        # Send to all users
        for user in users:
            await self.in_app_notifier.send(
                user=user,
                subject="System Alert",
                content={
                    "message": message,
                    "metadata": {"timestamp": datetime.utcnow().isoformat()}
                },
                category=NotificationCategory.SYSTEM,
                type=NotificationType.WARNING if priority == NotificationPriority.HIGH else NotificationType.INFO,
                priority=priority,
                expires_in_days=3
            )

    async def trigger_streak_reminder(self, user_id: int, current_streak: int):
        """
        Trigger daily streak reminder (if no activity today)

        Args:
            user_id: User ID
            current_streak: Current learning streak in days
        """

        # Get user
        user_query = select(User).where(User.id == user_id)
        result = await self.db.execute(user_query)
        user = result.scalar_one_or_none()

        if not user:
            return

        # Send reminder
        await self.in_app_notifier.send(
            user=user,
            subject="Keep Your Streak Alive!",
            content={
                "message": f"You're on a {current_streak} day streak! Complete a lesson today to keep it going.",
                "action_url": "/learn",
                "action_label": "Start Learning",
                "metadata": {"streak": current_streak}
            },
            category=NotificationCategory.ACHIEVEMENT,
            type=NotificationType.INFO,
            priority=NotificationPriority.MEDIUM,
            expires_in_days=1
        )

    async def trigger_trending_topic_alert(
        self,
        topic: str,
        article_count: int,
        user_ids: Optional[List[int]] = None
    ):
        """
        Alert users about trending topics

        Args:
            topic: Trending topic name
            article_count: Number of articles about this topic
            user_ids: Optional list of interested user IDs
        """

        # Get users (either specified or all active)
        if user_ids:
            users_query = select(User).where(User.id.in_(user_ids))
        else:
            # Skip if no specific users
            return

        result = await self.db.execute(users_query)
        users = result.scalars().all()

        # Send notifications
        for user in users:
            await self.in_app_notifier.send(
                user=user,
                subject=f"Trending: {topic}",
                content={
                    "message": f"{article_count} new articles about {topic}",
                    "action_url": f"/news?topic={topic}",
                    "action_label": "Explore Topic",
                    "metadata": {"topic": topic, "count": article_count}
                },
                category=NotificationCategory.NEW_CONTENT,
                type=NotificationType.INFO,
                priority=NotificationPriority.LOW,
                expires_in_days=2
            )

    # Helper Methods

    async def _find_interested_users(self, content: ScrapedContent) -> List[int]:
        """
        Find users who should be notified about new content based on their preferences.

        Matches users based on:
        - Preferred sources (e.g., 'El Tiempo', 'Semana')
        - Preferred categories (e.g., 'Politics', 'Economy')
        - Preferred topics from interests JSON field
        - Spanish level (content difficulty matching)

        Args:
            content: ScrapedContent object to match against

        Returns:
            List of user IDs who should be notified

        Example:
            >>> content = ScrapedContent(source='El Tiempo', category='Politics', ...)
            >>> user_ids = await triggers._find_interested_users(content)
            >>> # Returns users who have 'El Tiempo' in preferred_sources
            >>> # OR 'Politics' in preferred_categories
        """
        matching_user_ids = []

        # Get all active users with preferences
        users_query = select(User).where(User.is_active == True)
        result = await self.db.execute(users_query)
        users = result.scalars().all()

        for user in users:
            should_notify = False

            # Match by source preference
            if user.preferred_sources and content.source in user.preferred_sources:
                should_notify = True

            # Match by category preference
            if user.preferred_categories and content.category in user.preferred_categories:
                should_notify = True

            # Match by topics/interests
            if user.interests and content.tags:
                user_interests = set(user.interests if isinstance(user.interests, list) else [])
                content_tags = set(content.tags if isinstance(content.tags, list) else [])

                # If any tag matches any interest
                if user_interests.intersection(content_tags):
                    should_notify = True

            # Match by difficulty level (content not too hard)
            if user.spanish_level and content.difficulty_score:
                # Map CEFR levels to numeric scores (A1=1, A2=2, B1=3, B2=4, C1=5, C2=6)
                level_map = {'A1': 1, 'A2': 2, 'B1': 3, 'B2': 4, 'C1': 5, 'C2': 6}
                user_level = level_map.get(user.spanish_level, 3)  # Default B1

                # Content should be within user's level +/- 1
                # e.g., B1 user (3) gets content difficulty 2-4 (A2-B2)
                if abs(content.difficulty_score - user_level) <= 1.5:
                    should_notify = should_notify or True

            if should_notify:
                matching_user_ids.append(user.id)

        logger.info(f"Content {content.id} matched {len(matching_user_ids)} interested users")
        return matching_user_ids
