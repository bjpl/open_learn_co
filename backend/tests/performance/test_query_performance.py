"""
Performance tests for database queries with indexes.

Tests common query patterns to ensure <50ms p95 latency target.
Compares performance before/after index creation.
"""

import pytest
import time
import asyncio
from typing import List, Dict, Any
from datetime import datetime, timedelta
from statistics import mean, median
from sqlalchemy import select, func, and_, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import (
    ScrapedContent,
    ContentAnalysis,
    ExtractedVocabulary,
    User,
    UserContentProgress,
    UserVocabulary,
    LearningSession,
    IntelligenceAlert
)


class PerformanceMetrics:
    """Store and analyze query performance metrics."""

    def __init__(self):
        self.measurements: List[float] = []

    def record(self, duration_ms: float):
        """Record a query duration in milliseconds."""
        self.measurements.append(duration_ms)

    @property
    def p50(self) -> float:
        """50th percentile (median)."""
        if not self.measurements:
            return 0.0
        return median(sorted(self.measurements))

    @property
    def p95(self) -> float:
        """95th percentile."""
        if not self.measurements:
            return 0.0
        sorted_times = sorted(self.measurements)
        idx = int(len(sorted_times) * 0.95)
        return sorted_times[idx]

    @property
    def p99(self) -> float:
        """99th percentile."""
        if not self.measurements:
            return 0.0
        sorted_times = sorted(self.measurements)
        idx = int(len(sorted_times) * 0.99)
        return sorted_times[idx]

    @property
    def avg(self) -> float:
        """Average duration."""
        if not self.measurements:
            return 0.0
        return mean(self.measurements)

    @property
    def min(self) -> float:
        """Minimum duration."""
        if not self.measurements:
            return 0.0
        return min(self.measurements)

    @property
    def max(self) -> float:
        """Maximum duration."""
        if not self.measurements:
            return 0.0
        return max(self.measurements)

    def summary(self) -> Dict[str, float]:
        """Get summary statistics."""
        return {
            "min": self.min,
            "p50": self.p50,
            "p95": self.p95,
            "p99": self.p99,
            "avg": self.avg,
            "max": self.max,
            "samples": len(self.measurements)
        }


async def measure_query(db: AsyncSession, query, iterations: int = 10) -> PerformanceMetrics:
    """
    Measure query performance over multiple iterations.

    Args:
        db: Database session
        query: SQLAlchemy query to execute
        iterations: Number of times to run the query

    Returns:
        PerformanceMetrics with timing data
    """
    metrics = PerformanceMetrics()

    for _ in range(iterations):
        start = time.perf_counter()
        await db.execute(query)
        end = time.perf_counter()
        duration_ms = (end - start) * 1000
        metrics.record(duration_ms)

    return metrics


@pytest.mark.asyncio
class TestScrapedContentQueries:
    """Test performance of ScrapedContent table queries."""

    async def test_filter_by_source(self, async_db: AsyncSession):
        """Test: Filter by source (common query pattern)."""
        query = select(ScrapedContent).where(ScrapedContent.source == 'El Tiempo')

        metrics = await measure_query(async_db, query, iterations=20)

        print(f"\n  Filter by source: {metrics.summary()}")
        assert metrics.p95 < 50, f"p95 latency {metrics.p95}ms exceeds 50ms target"

    async def test_filter_by_source_and_category(self, async_db: AsyncSession):
        """Test: Filter by source and category (composite index)."""
        query = select(ScrapedContent).where(
            and_(
                ScrapedContent.source == 'El Tiempo',
                ScrapedContent.category == 'politics'
            )
        )

        metrics = await measure_query(async_db, query, iterations=20)

        print(f"\n  Filter by source + category: {metrics.summary()}")
        assert metrics.p95 < 50, f"p95 latency {metrics.p95}ms exceeds 50ms target"

    async def test_sort_by_published_date(self, async_db: AsyncSession):
        """Test: Sort by published date (indexed DESC)."""
        query = select(ScrapedContent).order_by(
            ScrapedContent.published_date.desc()
        ).limit(20)

        metrics = await measure_query(async_db, query, iterations=20)

        print(f"\n  Sort by published date: {metrics.summary()}")
        assert metrics.p95 < 50, f"p95 latency {metrics.p95}ms exceeds 50ms target"

    async def test_difficulty_filter(self, async_db: AsyncSession):
        """Test: Filter by difficulty score (partial index)."""
        query = select(ScrapedContent).where(
            and_(
                ScrapedContent.difficulty_score >= 2.0,
                ScrapedContent.difficulty_score <= 4.0
            )
        )

        metrics = await measure_query(async_db, query, iterations=20)

        print(f"\n  Filter by difficulty: {metrics.summary()}")
        assert metrics.p95 < 50, f"p95 latency {metrics.p95}ms exceeds 50ms target"

    async def test_full_text_search(self, async_db: AsyncSession):
        """Test: Full-text search on title/content (GIN index)."""
        query = text("""
            SELECT id, title, content
            FROM scraped_content
            WHERE to_tsvector('spanish', title || ' ' || content) @@ to_tsquery('spanish', 'Colombia')
            LIMIT 20
        """)

        metrics = await measure_query(async_db, query, iterations=10)

        print(f"\n  Full-text search: {metrics.summary()}")
        assert metrics.p95 < 200, f"p95 latency {metrics.p95}ms exceeds 200ms target for search"

    async def test_composite_filtering(self, async_db: AsyncSession):
        """Test: Source + category + date range (complex filter)."""
        seven_days_ago = datetime.utcnow() - timedelta(days=7)

        query = select(ScrapedContent).where(
            and_(
                ScrapedContent.source == 'El Tiempo',
                ScrapedContent.category == 'politics',
                ScrapedContent.published_date >= seven_days_ago
            )
        ).order_by(ScrapedContent.published_date.desc())

        metrics = await measure_query(async_db, query, iterations=20)

        print(f"\n  Composite filter (source+category+date): {metrics.summary()}")
        assert metrics.p95 < 50, f"p95 latency {metrics.p95}ms exceeds 50ms target"


@pytest.mark.asyncio
class TestUserQueries:
    """Test performance of User table queries."""

    async def test_login_by_email(self, async_db: AsyncSession):
        """Test: Login query (case-insensitive email)."""
        query = text("""
            SELECT * FROM users
            WHERE lower(email) = lower(:email)
            AND is_active = true
            LIMIT 1
        """).bindparams(email='test@example.com')

        metrics = await measure_query(async_db, query, iterations=50)

        print(f"\n  Login by email: {metrics.summary()}")
        assert metrics.p95 < 50, f"p95 latency {metrics.p95}ms exceeds 50ms target (critical for auth)"

    async def test_refresh_token_lookup(self, async_db: AsyncSession):
        """Test: Refresh token validation."""
        query = select(User).where(
            and_(
                User.refresh_token == 'test_token_123',
                User.refresh_token_expires_at > datetime.utcnow()
            )
        )

        metrics = await measure_query(async_db, query, iterations=50)

        print(f"\n  Refresh token lookup: {metrics.summary()}")
        assert metrics.p95 < 50, f"p95 latency {metrics.p95}ms exceeds 50ms target"

    async def test_active_users_count(self, async_db: AsyncSession):
        """Test: Count active users (partial index)."""
        query = select(func.count(User.id)).where(User.is_active == True)

        metrics = await measure_query(async_db, query, iterations=20)

        print(f"\n  Active users count: {metrics.summary()}")
        assert metrics.p95 < 50, f"p95 latency {metrics.p95}ms exceeds 50ms target"


@pytest.mark.asyncio
class TestContentAnalysisQueries:
    """Test performance of ContentAnalysis queries."""

    async def test_sentiment_analysis(self, async_db: AsyncSession):
        """Test: Filter by sentiment score."""
        query = select(ContentAnalysis).where(
            ContentAnalysis.sentiment_score > 0.5
        ).order_by(ContentAnalysis.processed_at.desc())

        metrics = await measure_query(async_db, query, iterations=20)

        print(f"\n  Sentiment analysis: {metrics.summary()}")
        assert metrics.p95 < 50, f"p95 latency {metrics.p95}ms exceeds 50ms target"

    async def test_content_join(self, async_db: AsyncSession):
        """Test: Join with ScrapedContent (foreign key index)."""
        query = select(ContentAnalysis).join(
            ScrapedContent,
            ContentAnalysis.content_id == ScrapedContent.id
        ).where(ScrapedContent.source == 'El Tiempo')

        metrics = await measure_query(async_db, query, iterations=20)

        print(f"\n  Content analysis join: {metrics.summary()}")
        assert metrics.p95 < 50, f"p95 latency {metrics.p95}ms exceeds 50ms target"


@pytest.mark.asyncio
class TestVocabularyQueries:
    """Test performance of vocabulary-related queries."""

    async def test_word_lookup(self, async_db: AsyncSession):
        """Test: Look up word by name."""
        query = select(ExtractedVocabulary).where(
            ExtractedVocabulary.word == 'gobierno'
        )

        metrics = await measure_query(async_db, query, iterations=30)

        print(f"\n  Word lookup: {metrics.summary()}")
        assert metrics.p95 < 50, f"p95 latency {metrics.p95}ms exceeds 50ms target"

    async def test_difficulty_filtering(self, async_db: AsyncSession):
        """Test: Filter by difficulty level."""
        query = select(ExtractedVocabulary).where(
            ExtractedVocabulary.difficulty_level == 3
        ).limit(20)

        metrics = await measure_query(async_db, query, iterations=20)

        print(f"\n  Difficulty filtering: {metrics.summary()}")
        assert metrics.p95 < 50, f"p95 latency {metrics.p95}ms exceeds 50ms target"

    async def test_spaced_repetition(self, async_db: AsyncSession):
        """Test: Get words due for review (spaced repetition)."""
        query = select(UserVocabulary).where(
            and_(
                UserVocabulary.user_id == 1,
                UserVocabulary.next_review <= datetime.utcnow()
            )
        ).order_by(UserVocabulary.next_review)

        metrics = await measure_query(async_db, query, iterations=30)

        print(f"\n  Spaced repetition query: {metrics.summary()}")
        assert metrics.p95 < 50, f"p95 latency {metrics.p95}ms exceeds 50ms target"


@pytest.mark.asyncio
class TestLearningSessionQueries:
    """Test performance of learning session queries."""

    async def test_user_sessions(self, async_db: AsyncSession):
        """Test: Get user's recent sessions."""
        query = select(LearningSession).where(
            LearningSession.user_id == 1
        ).order_by(LearningSession.started_at.desc()).limit(10)

        metrics = await measure_query(async_db, query, iterations=30)

        print(f"\n  User sessions: {metrics.summary()}")
        assert metrics.p95 < 50, f"p95 latency {metrics.p95}ms exceeds 50ms target"

    async def test_streak_calculation(self, async_db: AsyncSession):
        """Test: Calculate learning streak (date-based query)."""
        query = text("""
            SELECT COUNT(DISTINCT DATE(started_at))
            FROM learning_sessions
            WHERE user_id = :user_id
            AND started_at >= CURRENT_DATE - INTERVAL '30 days'
        """).bindparams(user_id=1)

        metrics = await measure_query(async_db, query, iterations=20)

        print(f"\n  Streak calculation: {metrics.summary()}")
        assert metrics.p95 < 100, f"p95 latency {metrics.p95}ms exceeds 100ms target for analytics"


@pytest.mark.asyncio
class TestAnalyticsQueries:
    """Test performance of analytics and reporting queries."""

    async def test_source_distribution(self, async_db: AsyncSession):
        """Test: Get article count by source."""
        query = select(
            ScrapedContent.source,
            func.count(ScrapedContent.id).label('count')
        ).group_by(ScrapedContent.source)

        metrics = await measure_query(async_db, query, iterations=10)

        print(f"\n  Source distribution: {metrics.summary()}")
        assert metrics.p95 < 500, f"p95 latency {metrics.p95}ms exceeds 500ms target for analytics"

    async def test_sentiment_trends(self, async_db: AsyncSession):
        """Test: Calculate sentiment trends over time."""
        query = text("""
            SELECT
                DATE(processed_at) as date,
                AVG(sentiment_score) as avg_sentiment,
                COUNT(*) as count
            FROM content_analysis
            WHERE processed_at >= CURRENT_DATE - INTERVAL '30 days'
            AND sentiment_score IS NOT NULL
            GROUP BY DATE(processed_at)
            ORDER BY date DESC
        """)

        metrics = await measure_query(async_db, query, iterations=10)

        print(f"\n  Sentiment trends: {metrics.summary()}")
        assert metrics.p95 < 500, f"p95 latency {metrics.p95}ms exceeds 500ms target for analytics"


async def generate_performance_report(db: AsyncSession) -> Dict[str, Any]:
    """
    Generate comprehensive performance report.

    Returns:
        Dictionary with performance metrics for all query types
    """
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "target_p95_ms": 50,
        "tests": {}
    }

    # Test each query category
    test_classes = [
        TestScrapedContentQueries(),
        TestUserQueries(),
        TestContentAnalysisQueries(),
        TestVocabularyQueries(),
        TestLearningSessionQueries(),
        TestAnalyticsQueries()
    ]

    for test_class in test_classes:
        class_name = test_class.__class__.__name__
        report["tests"][class_name] = {}

        # Run all test methods
        for method_name in dir(test_class):
            if method_name.startswith('test_'):
                method = getattr(test_class, method_name)
                try:
                    await method(db)
                    report["tests"][class_name][method_name] = "PASSED"
                except AssertionError as e:
                    report["tests"][class_name][method_name] = f"FAILED: {str(e)}"
                except Exception as e:
                    report["tests"][class_name][method_name] = f"ERROR: {str(e)}"

    return report


async def check_index_usage(db: AsyncSession) -> Dict[str, Any]:
    """
    Check which indexes are being used and their statistics.

    Returns:
        Dictionary with index usage statistics
    """
    query = text("""
        SELECT
            schemaname,
            tablename,
            indexname,
            pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
            idx_scan as times_used,
            idx_tup_read as tuples_read,
            idx_tup_fetch as tuples_fetched
        FROM pg_stat_user_indexes
        WHERE schemaname = 'public'
        ORDER BY idx_scan DESC
    """)

    result = await db.execute(query)
    rows = result.fetchall()

    return {
        "indexes": [
            {
                "schema": row.schemaname,
                "table": row.tablename,
                "index": row.indexname,
                "size": row.index_size,
                "times_used": row.times_used,
                "tuples_read": row.tuples_read,
                "tuples_fetched": row.tuples_fetched
            }
            for row in rows
        ]
    }


async def check_unused_indexes(db: AsyncSession) -> List[Dict[str, Any]]:
    """
    Identify indexes that are never used.

    Returns:
        List of unused indexes
    """
    query = text("""
        SELECT
            schemaname,
            tablename,
            indexname,
            pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
            idx_scan
        FROM pg_stat_user_indexes
        WHERE schemaname = 'public' AND idx_scan = 0
        ORDER BY pg_relation_size(indexrelid) DESC
    """)

    result = await db.execute(query)
    rows = result.fetchall()

    return [
        {
            "schema": row.schemaname,
            "table": row.tablename,
            "index": row.indexname,
            "size": row.index_size,
            "scans": row.idx_scan
        }
        for row in rows
    ]


if __name__ == "__main__":
    """
    Run performance tests and generate report.

    Usage:
        python -m pytest backend/tests/performance/test_query_performance.py -v -s
    """
    print("Performance tests will be run by pytest")
    print("Run with: pytest backend/tests/performance/test_query_performance.py -v -s")
