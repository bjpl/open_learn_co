"""
Digest Notifier
Sends daily/weekly digest emails with aggregated content
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy import select, and_, func
import logging

from app.services.notifiers.email_notifier import EmailNotifier
from app.database.models import User, ScrapedContent, UserVocabulary, LearningSession
from app.database.notification_models import NotificationPreference


logger = logging.getLogger(__name__)


class DigestNotifier(EmailNotifier):
    """Daily and weekly digest email notifications"""

    async def send_daily_digest(self, user: User) -> bool:
        """Send daily digest email to a user"""

        # Check if daily digest is enabled
        prefs = await self._get_preferences(user.id)
        if not prefs or not prefs.email_digest_enabled:
            logger.info(f"Daily digest disabled for user {user.id}")
            return False

        # Gather digest content
        content = await self._gather_daily_content(user)

        if not content.get("has_content"):
            logger.info(f"No content for daily digest for user {user.id}")
            return False

        # Send email using daily_digest template
        subject = f"Your Daily OpenLearn Digest - {datetime.now().strftime('%B %d, %Y')}"

        return await self.send(
            user=user,
            subject=subject,
            content=content,
            template="daily_digest"
        )

    async def send_weekly_summary(self, user: User) -> bool:
        """Send weekly summary email to a user"""

        # Check if weekly summary is enabled
        prefs = await self._get_preferences(user.id)
        if not prefs or not prefs.email_weekly_enabled:
            logger.info(f"Weekly summary disabled for user {user.id}")
            return False

        # Gather weekly content
        content = await self._gather_weekly_content(user)

        if not content.get("has_content"):
            logger.info(f"No content for weekly summary for user {user.id}")
            return False

        # Send email using weekly_summary template
        subject = f"Your Weekly OpenLearn Summary - Week of {datetime.now().strftime('%B %d')}"

        return await self.send(
            user=user,
            subject=subject,
            content=content,
            template="weekly_summary"
        )

    async def _gather_daily_content(self, user: User) -> Dict[str, Any]:
        """Gather content for daily digest"""

        yesterday = datetime.utcnow() - timedelta(days=1)

        # Get new articles (last 24 hours)
        new_articles_query = select(ScrapedContent).where(
            ScrapedContent.scraped_at >= yesterday
        ).order_by(ScrapedContent.sentiment_score.desc()).limit(10)

        result = await self.db.execute(new_articles_query)
        new_articles = result.scalars().all()

        # Get vocabulary to review (due today)
        vocab_query = select(UserVocabulary).where(
            and_(
                UserVocabulary.user_id == user.id,
                UserVocabulary.next_review <= datetime.utcnow(),
                UserVocabulary.mastery_level < 1.0
            )
        ).limit(5)

        result = await self.db.execute(vocab_query)
        vocab_to_review = result.scalars().all()

        # Get learning streak
        streak_query = select(func.count(func.distinct(
            func.date(LearningSession.started_at)
        ))).where(
            and_(
                LearningSession.user_id == user.id,
                LearningSession.started_at >= datetime.utcnow() - timedelta(days=30)
            )
        )

        result = await self.db.execute(streak_query)
        streak_days = result.scalar() or 0

        has_content = len(new_articles) > 0 or len(vocab_to_review) > 0

        return {
            "has_content": has_content,
            "new_articles": [
                {
                    "title": article.title,
                    "source": article.source,
                    "url": article.source_url,
                    "difficulty": article.difficulty_score or 0,
                }
                for article in new_articles[:5]
            ],
            "article_count": len(new_articles),
            "vocab_to_review": [
                {
                    "word": v.vocabulary.word if hasattr(v, 'vocabulary') else "",
                    "definition": v.vocabulary.spanish_definition if hasattr(v, 'vocabulary') else "",
                }
                for v in vocab_to_review
            ],
            "vocab_count": len(vocab_to_review),
            "streak_days": streak_days,
            "date": datetime.now().strftime("%B %d, %Y"),
        }

    async def _gather_weekly_content(self, user: User) -> Dict[str, Any]:
        """Gather content for weekly summary"""

        last_week = datetime.utcnow() - timedelta(days=7)

        # Get learning sessions this week
        sessions_query = select(LearningSession).where(
            and_(
                LearningSession.user_id == user.id,
                LearningSession.started_at >= last_week
            )
        )

        result = await self.db.execute(sessions_query)
        sessions = result.scalars().all()

        # Calculate stats
        total_time = sum(s.duration_seconds or 0 for s in sessions)
        total_items = sum(s.items_completed or 0 for s in sessions)
        avg_score = sum(s.score or 0 for s in sessions) / len(sessions) if sessions else 0

        # Get new vocabulary learned
        vocab_query = select(UserVocabulary).where(
            and_(
                UserVocabulary.user_id == user.id,
                UserVocabulary.first_seen >= last_week
            )
        )

        result = await self.db.execute(vocab_query)
        new_vocab = result.scalars().all()

        # Get top articles by engagement
        # (This would require tracking which articles were read)

        has_content = len(sessions) > 0 or len(new_vocab) > 0

        return {
            "has_content": has_content,
            "sessions_count": len(sessions),
            "total_time_minutes": total_time // 60,
            "items_completed": total_items,
            "avg_score": round(avg_score * 100, 1),
            "new_vocab_count": len(new_vocab),
            "week_start": last_week.strftime("%B %d"),
            "week_end": datetime.now().strftime("%B %d, %Y"),
        }

    async def _get_preferences(self, user_id: int) -> Optional[NotificationPreference]:
        """Get notification preferences for user"""

        from app.services.notification_service import NotificationService

        service = NotificationService(self.db)
        return await service.get_user_preferences(user_id)
