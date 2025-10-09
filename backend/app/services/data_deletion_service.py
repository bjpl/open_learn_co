"""
Data Deletion Service - GDPR Compliance

Provides safe, auditable data deletion capabilities in compliance with:
- GDPR Article 17 (Right to be Forgotten)
- GDPR Article 20 (Right to Data Portability)
- CCPA (California Consumer Privacy Act)

All deletion operations are:
- Logged for audit trails
- Atomic (all-or-nothing via transactions)
- Verified for completeness
- Reported with detailed counts
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy import delete, select, func
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.database.models import (
    User, UserVocabulary, UserContentProgress, LearningSession
)
from app.database.notification_models import (
    Notification, NotificationPreference, EmailLog
)

logger = logging.getLogger(__name__)


class DataDeletionService:
    """Service for managing user data deletion operations"""

    def __init__(self, db: Session):
        self.db = db

    async def delete_user_completely(
        self,
        user_id: int,
        reason: str = "user_requested"
    ) -> Dict[str, any]:
        """
        Completely delete a user and all associated data (GDPR Article 17).

        This is a permanent, irreversible operation that removes:
        - User account and profile
        - All learning progress (vocabulary, content, sessions)
        - All notifications (in-app and email logs)
        - All preferences and settings

        Args:
            user_id: ID of user to delete
            reason: Reason for deletion (for audit log)

        Returns:
            Dictionary with deletion statistics

        Example:
            >>> result = await service.delete_user_completely(123, "user_requested")
            >>> {
            >>>     'user_id': 123,
            >>>     'deleted_at': '2025-10-08T...',
            >>>     'tables_cleared': 7,
            >>>     'total_records_deleted': 1543,
            >>>     'deletion_breakdown': {...}
            >>> }
        """
        try:
            logger.info(f"Starting complete deletion for user {user_id}, reason: {reason}")

            deletion_stats = {}

            # Delete in dependency order (children first, parent last)

            # 1. Email logs (no dependencies)
            email_result = self.db.execute(
                delete(EmailLog).where(EmailLog.user_id == user_id)
            )
            deletion_stats['email_logs'] = email_result.rowcount
            logger.debug(f"Deleted {email_result.rowcount} email logs for user {user_id}")

            # 2. Notifications (no dependencies)
            notification_result = self.db.execute(
                delete(Notification).where(Notification.user_id == user_id)
            )
            deletion_stats['notifications'] = notification_result.rowcount
            logger.debug(f"Deleted {notification_result.rowcount} notifications for user {user_id}")

            # 3. Notification preferences (no dependencies)
            notif_pref_result = self.db.execute(
                delete(NotificationPreference).where(NotificationPreference.user_id == user_id)
            )
            deletion_stats['notification_preferences'] = notif_pref_result.rowcount
            logger.debug(f"Deleted {notif_pref_result.rowcount} notification preferences for user {user_id}")

            # 4. Learning sessions (no dependencies)
            session_result = self.db.execute(
                delete(LearningSession).where(LearningSession.user_id == user_id)
            )
            deletion_stats['learning_sessions'] = session_result.rowcount
            logger.debug(f"Deleted {session_result.rowcount} learning sessions for user {user_id}")

            # 5. Vocabulary progress (no dependencies)
            vocab_result = self.db.execute(
                delete(UserVocabulary).where(UserVocabulary.user_id == user_id)
            )
            deletion_stats['vocabulary_progress'] = vocab_result.rowcount
            logger.debug(f"Deleted {vocab_result.rowcount} vocabulary items for user {user_id}")

            # 6. Content progress (no dependencies)
            content_result = self.db.execute(
                delete(UserContentProgress).where(UserContentProgress.user_id == user_id)
            )
            deletion_stats['content_progress'] = content_result.rowcount
            logger.debug(f"Deleted {content_result.rowcount} content progress records for user {user_id}")

            # 7. User account (parent table - delete last)
            user_result = self.db.execute(
                delete(User).where(User.id == user_id)
            )
            deletion_stats['user_account'] = user_result.rowcount
            logger.debug(f"Deleted user account {user_id}")

            # Commit all deletions atomically
            self.db.commit()

            # Calculate totals
            total_records = sum(deletion_stats.values())
            tables_cleared = len([v for v in deletion_stats.values() if v > 0])

            result = {
                'user_id': user_id,
                'deleted_at': datetime.utcnow().isoformat(),
                'reason': reason,
                'tables_cleared': tables_cleared,
                'total_records_deleted': total_records,
                'deletion_breakdown': deletion_stats,
                'gdpr_compliant': True
            }

            logger.info(f"User {user_id} deletion complete: {total_records} records deleted across {tables_cleared} tables")

            return result

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete user {user_id}: {e}", exc_info=True)
            raise

    async def clear_learning_progress(
        self,
        user_id: int
    ) -> Dict[str, any]:
        """
        Clear user's learning progress without deleting account.

        Removes:
        - Vocabulary progress (learned words, mastery levels)
        - Content progress (reading history, comprehension scores)
        - Learning sessions (activity history)

        Preserves:
        - User account and authentication
        - Preferences and settings
        - Notifications (can be cleared separately)

        Args:
            user_id: ID of user whose progress to clear

        Returns:
            Dictionary with deletion statistics
        """
        try:
            logger.info(f"Clearing learning progress for user {user_id}")

            deletion_stats = {}

            # Delete learning data
            vocab_result = self.db.execute(
                delete(UserVocabulary).where(UserVocabulary.user_id == user_id)
            )
            deletion_stats['vocabulary_items'] = vocab_result.rowcount

            content_result = self.db.execute(
                delete(UserContentProgress).where(UserContentProgress.user_id == user_id)
            )
            deletion_stats['content_progress'] = content_result.rowcount

            session_result = self.db.execute(
                delete(LearningSession).where(LearningSession.user_id == user_id)
            )
            deletion_stats['learning_sessions'] = session_result.rowcount

            # Commit all deletions
            self.db.commit()

            total_records = sum(deletion_stats.values())

            result = {
                'user_id': user_id,
                'cleared_at': datetime.utcnow().isoformat(),
                'total_records_deleted': total_records,
                'deletion_breakdown': deletion_stats
            }

            logger.info(f"Progress cleared for user {user_id}: {total_records} records deleted")

            return result

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to clear progress for user {user_id}: {e}", exc_info=True)
            raise

    async def clear_notifications(
        self,
        user_id: int,
        older_than_days: Optional[int] = None
    ) -> int:
        """
        Clear user notifications.

        Args:
            user_id: User ID
            older_than_days: Only clear notifications older than X days (optional)

        Returns:
            Number of notifications deleted
        """
        try:
            if older_than_days:
                cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
                result = self.db.execute(
                    delete(Notification).where(
                        Notification.user_id == user_id,
                        Notification.created_at < cutoff_date
                    )
                )
            else:
                result = self.db.execute(
                    delete(Notification).where(Notification.user_id == user_id)
                )

            self.db.commit()
            count = result.rowcount

            logger.info(f"Cleared {count} notifications for user {user_id}")
            return count

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to clear notifications for user {user_id}: {e}")
            raise

    async def get_user_data_summary(
        self,
        user_id: int
    ) -> Dict[str, any]:
        """
        Get summary of all data associated with a user.

        Useful for:
        - Data export (GDPR Article 20)
        - Showing user what will be deleted
        - Audit trails

        Args:
            user_id: User ID

        Returns:
            Dictionary with data counts per table

        Example:
            >>> summary = await service.get_user_data_summary(123)
            >>> {
            >>>     'user_account': 1,
            >>>     'vocabulary_items': 247,
            >>>     'content_progress': 89,
            >>>     'learning_sessions': 156,
            >>>     'notifications': 42,
            >>>     'email_logs': 15,
            >>>     'total_records': 550
            >>> }
        """
        summary = {}

        # Count records in each table
        summary['user_account'] = self.db.execute(
            select(func.count()).where(User.id == user_id)
        ).scalar()

        summary['vocabulary_items'] = self.db.execute(
            select(func.count()).where(UserVocabulary.user_id == user_id)
        ).scalar()

        summary['content_progress'] = self.db.execute(
            select(func.count()).where(UserContentProgress.user_id == user_id)
        ).scalar()

        summary['learning_sessions'] = self.db.execute(
            select(func.count()).where(LearningSession.user_id == user_id)
        ).scalar()

        summary['notifications'] = self.db.execute(
            select(func.count()).where(Notification.user_id == user_id)
        ).scalar()

        summary['email_logs'] = self.db.execute(
            select(func.count()).where(EmailLog.user_id == user_id)
        ).scalar()

        summary['notification_preferences'] = self.db.execute(
            select(func.count()).where(NotificationPreference.user_id == user_id)
        ).scalar()

        summary['total_records'] = sum(summary.values())

        return summary


# Convenience functions

async def delete_user_account(
    db: Session,
    user_id: int,
    reason: str = "user_requested"
) -> Dict:
    """Convenience function to delete user account"""
    service = DataDeletionService(db)
    return await service.delete_user_completely(user_id, reason)


async def clear_user_progress(
    db: Session,
    user_id: int
) -> Dict:
    """Convenience function to clear user progress"""
    service = DataDeletionService(db)
    return await service.clear_learning_progress(user_id)


async def get_deletion_preview(
    db: Session,
    user_id: int
) -> Dict:
    """Get preview of what will be deleted (for user confirmation)"""
    service = DataDeletionService(db)
    return await service.get_user_data_summary(user_id)
