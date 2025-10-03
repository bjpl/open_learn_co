"""
Notification Scheduler Jobs
Scheduled tasks for sending digests, reminders, and cleanup
"""

import logging
from datetime import datetime, timedelta
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_async_session
from app.database.models import User
from app.database.notification_models import NotificationPreference
from app.services.notifiers.digest_notifier import DigestNotifier
from app.services.notification_triggers import NotificationTriggers
from app.services.notification_service import NotificationService


logger = logging.getLogger(__name__)


async def send_daily_digests():
    """
    Send daily digest emails to users who have them enabled
    Runs once per day (configured in scheduler)
    """

    logger.info("Starting daily digest job")

    async for db in get_async_session():
        try:
            # Get users with daily digest enabled
            query = select(User).join(NotificationPreference).where(
                and_(
                    NotificationPreference.email_digest_enabled == True,
                    User.is_active == True
                )
            )

            result = await db.execute(query)
            users = result.scalars().all()

            logger.info(f"Sending daily digests to {len(users)} users")

            # Send digests
            notifier = DigestNotifier(db)
            success_count = 0
            fail_count = 0

            for user in users:
                try:
                    # TODO: Check user timezone and send at their configured time
                    # For now, send to all at once
                    if await notifier.send_daily_digest(user):
                        success_count += 1
                    else:
                        fail_count += 1

                except Exception as e:
                    logger.error(f"Failed to send daily digest to user {user.id}: {e}")
                    fail_count += 1

            logger.info(f"Daily digest job complete: {success_count} sent, {fail_count} failed")

        except Exception as e:
            logger.error(f"Error in daily digest job: {e}")
        finally:
            await db.close()


async def send_weekly_summaries():
    """
    Send weekly summary emails to users who have them enabled
    Runs once per week (Monday mornings)
    """

    logger.info("Starting weekly summary job")

    async for db in get_async_session():
        try:
            # Get users with weekly summary enabled
            query = select(User).join(NotificationPreference).where(
                and_(
                    NotificationPreference.email_weekly_enabled == True,
                    User.is_active == True
                )
            )

            result = await db.execute(query)
            users = result.scalars().all()

            logger.info(f"Sending weekly summaries to {len(users)} users")

            # Send summaries
            notifier = DigestNotifier(db)
            success_count = 0
            fail_count = 0

            for user in users:
                try:
                    if await notifier.send_weekly_summary(user):
                        success_count += 1
                    else:
                        fail_count += 1

                except Exception as e:
                    logger.error(f"Failed to send weekly summary to user {user.id}: {e}")
                    fail_count += 1

            logger.info(f"Weekly summary job complete: {success_count} sent, {fail_count} failed")

        except Exception as e:
            logger.error(f"Error in weekly summary job: {e}")
        finally:
            await db.close()


async def send_vocabulary_reminders():
    """
    Send vocabulary review reminders to users who have words due
    Runs multiple times per day
    """

    logger.info("Starting vocabulary reminder job")

    async for db in get_async_session():
        try:
            from app.database.models import UserVocabulary

            # Get users with vocabulary due for review
            query = select(User).join(UserVocabulary).where(
                and_(
                    UserVocabulary.next_review <= datetime.utcnow(),
                    UserVocabulary.mastery_level < 1.0,
                    User.is_active == True
                )
            ).distinct()

            result = await db.execute(query)
            users = result.scalars().all()

            logger.info(f"Sending vocabulary reminders to {len(users)} users")

            # Send reminders
            triggers = NotificationTriggers(db)
            count = 0

            for user in users:
                try:
                    await triggers.trigger_vocabulary_reminder(user.id)
                    count += 1
                except Exception as e:
                    logger.error(f"Failed to send vocabulary reminder to user {user.id}: {e}")

            logger.info(f"Vocabulary reminder job complete: {count} sent")

        except Exception as e:
            logger.error(f"Error in vocabulary reminder job: {e}")
        finally:
            await db.close()


async def cleanup_old_notifications():
    """
    Clean up old notifications (older than 30 days)
    Runs daily
    """

    logger.info("Starting notification cleanup job")

    async for db in get_async_session():
        try:
            service = NotificationService(db)

            # Clean up old notifications
            deleted = await service.cleanup_old_notifications(days=30)
            logger.info(f"Deleted {deleted} old notifications")

            # Clean up expired notifications
            expired = await service.cleanup_expired_notifications()
            logger.info(f"Deleted {expired} expired notifications")

            logger.info(f"Notification cleanup complete: {deleted + expired} total deleted")

        except Exception as e:
            logger.error(f"Error in notification cleanup job: {e}")
        finally:
            await db.close()


async def send_streak_reminders():
    """
    Send learning streak reminders to users who haven't studied today
    Runs in the evening (8pm)
    """

    logger.info("Starting streak reminder job")

    async for db in get_async_session():
        try:
            from app.database.models import LearningSession
            from sqlalchemy import func

            # Get users who have an active streak but no activity today
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

            # Users with past sessions but none today
            subquery = select(LearningSession.user_id).where(
                LearningSession.started_at >= today_start
            ).subquery()

            query = select(User).where(
                and_(
                    User.is_active == True,
                    ~User.id.in_(select(subquery.c.user_id))
                )
            )

            result = await db.execute(query)
            users = result.scalars().all()

            logger.info(f"Sending streak reminders to {len(users)} users")

            # Send reminders
            triggers = NotificationTriggers(db)
            count = 0

            for user in users:
                try:
                    # Calculate current streak (simplified)
                    # TODO: Implement proper streak calculation
                    streak = 0
                    await triggers.trigger_streak_reminder(user.id, streak)
                    count += 1
                except Exception as e:
                    logger.error(f"Failed to send streak reminder to user {user.id}: {e}")

            logger.info(f"Streak reminder job complete: {count} sent")

        except Exception as e:
            logger.error(f"Error in streak reminder job: {e}")
        finally:
            await db.close()


# Job registration for APScheduler
NOTIFICATION_JOBS = [
    {
        "func": send_daily_digests,
        "trigger": "cron",
        "hour": 8,
        "minute": 0,
        "id": "daily_digests",
        "name": "Send Daily Digests",
        "replace_existing": True
    },
    {
        "func": send_weekly_summaries,
        "trigger": "cron",
        "day_of_week": "mon",
        "hour": 8,
        "minute": 0,
        "id": "weekly_summaries",
        "name": "Send Weekly Summaries",
        "replace_existing": True
    },
    {
        "func": send_vocabulary_reminders,
        "trigger": "cron",
        "hour": "*/4",  # Every 4 hours
        "minute": 0,
        "id": "vocabulary_reminders",
        "name": "Send Vocabulary Reminders",
        "replace_existing": True
    },
    {
        "func": cleanup_old_notifications,
        "trigger": "cron",
        "hour": 2,
        "minute": 0,
        "id": "cleanup_notifications",
        "name": "Cleanup Old Notifications",
        "replace_existing": True
    },
    {
        "func": send_streak_reminders,
        "trigger": "cron",
        "hour": 20,
        "minute": 0,
        "id": "streak_reminders",
        "name": "Send Streak Reminders",
        "replace_existing": True
    }
]
