"""
Learning Streak Calculator

Calculates and tracks user learning streaks with timezone awareness.
Supports daily streaks, weekly goals, and longest streak tracking.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, List
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from zoneinfo import ZoneInfo

from app.database.models import LearningSession, User
from app.utils.timezone_utils import get_start_of_day_utc, get_end_of_day_utc, get_user_timezone


class StreakCalculator:
    """Calculate and manage user learning streaks"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_current_streak(
        self,
        user_id: int,
        user_timezone: Optional[str] = None
    ) -> int:
        """
        Calculate user's current learning streak in days.

        A streak is maintained by having at least one learning session
        per day (in the user's local timezone).

        Args:
            user_id: User ID
            user_timezone: User's timezone (defaults to UTC if not provided)

        Returns:
            Current streak in days

        Example:
            >>> streak = await calculator.calculate_current_streak(123, 'America/Bogota')
            >>> print(f"Current streak: {streak} days")
        """
        # Get user's sessions ordered by start time (descending)
        query = select(LearningSession).where(
            LearningSession.user_id == user_id
        ).order_by(LearningSession.started_at.desc())

        result = await self.db.execute(query)
        sessions = result.scalars().all()

        if not sessions:
            return 0

        # Group sessions by date in user's timezone
        session_dates = set()
        for session in sessions:
            # Convert UTC session time to user's local date
            session_utc = session.started_at.replace(tzinfo=ZoneInfo('UTC'))
            user_tz = get_user_timezone(user_timezone)
            local_time = session_utc.astimezone(user_tz)
            session_dates.add(local_time.date())

        # Sort dates
        sorted_dates = sorted(session_dates, reverse=True)

        # Get today in user's timezone
        today_utc = datetime.now(ZoneInfo('UTC'))
        user_tz = get_user_timezone(user_timezone)
        today_local = today_utc.astimezone(user_tz).date()

        # Check if there's activity today or yesterday
        # (Streak is maintained if you studied yesterday and haven't yet today)
        if not sorted_dates:
            return 0

        most_recent_date = sorted_dates[0]
        yesterday_local = today_local - timedelta(days=1)

        # Streak broken if most recent session is more than 1 day ago
        if most_recent_date < yesterday_local:
            return 0

        # Count consecutive days
        streak = 0
        expected_date = today_local if most_recent_date == today_local else yesterday_local

        for session_date in sorted_dates:
            if session_date == expected_date:
                streak += 1
                expected_date -= timedelta(days=1)
            elif session_date < expected_date:
                # Gap found, streak ends
                break

        return streak

    async def calculate_longest_streak(
        self,
        user_id: int,
        user_timezone: Optional[str] = None
    ) -> int:
        """
        Calculate user's longest ever learning streak.

        Args:
            user_id: User ID
            user_timezone: User's timezone

        Returns:
            Longest streak in days
        """
        # Get all sessions
        query = select(LearningSession).where(
            LearningSession.user_id == user_id
        ).order_by(LearningSession.started_at.asc())

        result = await self.db.execute(query)
        sessions = result.scalars().all()

        if not sessions:
            return 0

        # Group sessions by date
        session_dates = set()
        for session in sessions:
            session_utc = session.started_at.replace(tzinfo=ZoneInfo('UTC'))
            user_tz = get_user_timezone(user_timezone)
            local_time = session_utc.astimezone(user_tz)
            session_dates.add(local_time.date())

        # Sort dates
        sorted_dates = sorted(session_dates)

        # Find longest consecutive sequence
        if not sorted_dates:
            return 0

        max_streak = 1
        current_streak = 1
        expected_date = sorted_dates[0] + timedelta(days=1)

        for i in range(1, len(sorted_dates)):
            if sorted_dates[i] == expected_date:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 1

            expected_date = sorted_dates[i] + timedelta(days=1)

        return max_streak

    async def has_activity_today(
        self,
        user_id: int,
        user_timezone: Optional[str] = None
    ) -> bool:
        """
        Check if user has any learning activity today.

        Args:
            user_id: User ID
            user_timezone: User's timezone

        Returns:
            True if user has studied today
        """
        # Get today's date range in user's timezone
        start_of_day_utc = get_start_of_day_utc(user_timezone, days_ago=0)
        end_of_day_utc = get_end_of_day_utc(user_timezone, days_ago=0)

        # Query sessions within today
        query = select(func.count()).where(
            and_(
                LearningSession.user_id == user_id,
                LearningSession.started_at >= start_of_day_utc,
                LearningSession.started_at <= end_of_day_utc
            )
        )

        result = await self.db.execute(query)
        count = result.scalar()

        return count > 0

    async def get_streak_stats(
        self,
        user_id: int,
        user_timezone: Optional[str] = None
    ) -> Dict:
        """
        Get comprehensive streak statistics for a user.

        Args:
            user_id: User ID
            user_timezone: User's timezone

        Returns:
            Dictionary with streak statistics

        Example:
            >>> stats = await calculator.get_streak_stats(123, 'America/Bogota')
            >>> {
            >>>     'current_streak': 7,
            >>>     'longest_streak': 21,
            >>>     'total_days_studied': 45,
            >>>     'studied_today': True,
            >>>     'streak_at_risk': False,
            >>>     'days_until_next_milestone': 3  # To reach 10-day streak
            >>> }
        """
        current_streak = await self.calculate_current_streak(user_id, user_timezone)
        longest_streak = await self.calculate_longest_streak(user_id, user_timezone)
        studied_today = await self.has_activity_today(user_id, user_timezone)

        # Get total unique days studied
        query = select(LearningSession).where(
            LearningSession.user_id == user_id
        )
        result = await self.db.execute(query)
        sessions = result.scalars().all()

        session_dates = set()
        for session in sessions:
            session_utc = session.started_at.replace(tzinfo=ZoneInfo('UTC'))
            user_tz = get_user_timezone(user_timezone)
            local_time = session_utc.astimezone(user_tz)
            session_dates.add(local_time.date())

        total_days_studied = len(session_dates)

        # Calculate next milestone (5, 10, 15, 20, 30, 50, 100 days)
        milestones = [5, 10, 15, 20, 30, 50, 100, 200, 365]
        next_milestone = next((m for m in milestones if m > current_streak), None)
        days_until_milestone = (next_milestone - current_streak) if next_milestone else 0

        return {
            'current_streak': current_streak,
            'longest_streak': longest_streak,
            'total_days_studied': total_days_studied,
            'studied_today': studied_today,
            'streak_at_risk': current_streak > 0 and not studied_today,
            'next_milestone': next_milestone,
            'days_until_next_milestone': days_until_milestone,
        }

    async def will_lose_streak_tomorrow(
        self,
        user_id: int,
        user_timezone: Optional[str] = None
    ) -> bool:
        """
        Check if user will lose their streak if they don't study today.

        Args:
            user_id: User ID
            user_timezone: User's timezone

        Returns:
            True if user has a streak and hasn't studied today
        """
        current_streak = await self.calculate_current_streak(user_id, user_timezone)
        studied_today = await self.has_activity_today(user_id, user_timezone)

        return current_streak > 0 and not studied_today

    async def get_streak_percentile(
        self,
        user_id: int,
        user_timezone: Optional[str] = None
    ) -> float:
        """
        Get user's streak percentile compared to all users.

        Args:
            user_id: User ID
            user_timezone: User's timezone

        Returns:
            Percentile (0-100) where 100 is the highest

        Example:
            >>> percentile = await calculator.get_streak_percentile(123)
            >>> print(f"You're in the top {100 - percentile:.0f}% of learners!")
        """
        user_streak = await self.calculate_current_streak(user_id, user_timezone)

        # Get all active users
        users_query = select(User).where(User.is_active == True)
        result = await self.db.execute(users_query)
        all_users = result.scalars().all()

        if not all_users:
            return 100.0

        # Calculate streaks for all users (cached in production)
        user_streaks = []
        for user in all_users:
            streak = await self.calculate_current_streak(user.id, None)
            user_streaks.append(streak)

        # Count users with lower streak
        users_below = sum(1 for s in user_streaks if s < user_streak)
        percentile = (users_below / len(user_streaks)) * 100 if user_streaks else 0

        return round(percentile, 1)


# Convenience functions for common use cases

async def get_current_streak(
    db: AsyncSession,
    user_id: int,
    user_timezone: Optional[str] = None
) -> int:
    """Get user's current streak (convenience function)"""
    calculator = StreakCalculator(db)
    return await calculator.calculate_current_streak(user_id, user_timezone)


async def get_streak_stats(
    db: AsyncSession,
    user_id: int,
    user_timezone: Optional[str] = None
) -> Dict:
    """Get user's streak statistics (convenience function)"""
    calculator = StreakCalculator(db)
    return await calculator.get_streak_stats(user_id, user_timezone)


async def should_send_streak_reminder(
    db: AsyncSession,
    user_id: int,
    user_timezone: Optional[str] = None
) -> bool:
    """
    Check if user should receive streak reminder.

    Returns True if:
    - User has an active streak (> 0 days)
    - User hasn't studied today
    - Current time is evening (after 6pm user's local time)
    """
    calculator = StreakCalculator(db)
    will_lose = await calculator.will_lose_streak_tomorrow(user_id, user_timezone)

    if not will_lose:
        return False

    # Check if it's evening in user's timezone
    from app.utils.timezone_utils import get_user_current_time
    user_now = get_user_current_time(user_timezone)

    # Send reminders between 6pm and 10pm
    return 18 <= user_now.hour < 22
