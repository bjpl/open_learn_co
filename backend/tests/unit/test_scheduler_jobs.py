"""
Comprehensive Scheduler Jobs Tests

Tests for:
- Job execution with retry logic
- Exponential backoff calculation
- Rate limiting and delays
- Job status tracking
- Scheduler metrics
- Manual scrape triggering
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncio

from app.services.scheduler_jobs import (
    execute_scraper_with_retry,
    calculate_backoff_delay,
    get_job_status,
    get_scheduler_metrics,
    trigger_manual_scrape,
    cleanup_old_executions,
    _track_execution,
    _track_failure,
    _job_executions,
    _job_failures,
)
from app.config.scheduler_config import SCRAPER_TIERS, RETRY_CONFIG


class TestBackoffCalculation:
    """Test exponential backoff delay calculation"""

    def test_calculate_backoff_first_retry(self):
        """First retry should use initial delay"""
        delay = calculate_backoff_delay(1)

        # First retry: base_delay * (2^0) = base_delay
        assert delay >= RETRY_CONFIG['initial_delay']
        assert delay <= RETRY_CONFIG['initial_delay'] * 1.2  # Allow for jitter

    def test_calculate_backoff_exponential_growth(self):
        """Backoff delay should grow exponentially"""
        delay1 = calculate_backoff_delay(1)
        delay2 = calculate_backoff_delay(2)
        delay3 = calculate_backoff_delay(3)

        # Each delay should be roughly double (allowing for jitter)
        assert delay2 > delay1
        assert delay3 > delay2

    def test_calculate_backoff_max_delay_cap(self):
        """Backoff delay should not exceed max delay"""
        # Very high attempt number
        delay = calculate_backoff_delay(20)

        # Should be capped at max_delay plus jitter
        assert delay <= RETRY_CONFIG['max_delay'] * 1.2

    def test_calculate_backoff_jitter_adds_randomness(self):
        """Backoff with jitter should produce different delays"""
        delays = [calculate_backoff_delay(5) for _ in range(10)]

        # Should have some variation due to jitter
        unique_delays = set(delays)
        assert len(unique_delays) > 1

    def test_calculate_backoff_progressive_values(self):
        """Test backoff progression matches expected pattern"""
        base = RETRY_CONFIG['initial_delay']
        exp_base = RETRY_CONFIG['exponential_base']

        for attempt in range(1, 6):
            delay = calculate_backoff_delay(attempt)
            expected_min = min(base * (exp_base ** (attempt - 1)), RETRY_CONFIG['max_delay'])

            # Should be at least the expected minimum
            assert delay >= expected_min * 0.9  # Allow some tolerance


class TestScraperExecution:
    """Test scraper execution with retry logic"""

    @pytest.mark.asyncio
    async def test_execute_scraper_success_first_try(self):
        """Successful scrape on first attempt"""
        source_config = {
            'name': 'Test Source',
            'url': 'http://example.com'
        }

        # Mock successful scraper
        mock_scraper = AsyncMock()
        mock_scraper.scrape = AsyncMock(return_value=[
            Mock(title="Article 1"),
            Mock(title="Article 2")
        ])

        mock_scraper_class = Mock(return_value=mock_scraper)
        mock_scraper_class.__aenter__ = AsyncMock(return_value=mock_scraper)
        mock_scraper_class.__aexit__ = AsyncMock()

        mock_db = Mock()
        mock_db.add = Mock()
        mock_db.commit = Mock()

        with patch('app.services.scheduler_jobs.SCRAPER_REGISTRY', {'Test Source': mock_scraper_class}):
            with patch('app.services.scheduler_jobs.get_db', return_value=mock_db):
                result = await execute_scraper_with_retry(
                    'Test Source',
                    source_config,
                    tier='high'
                )

        assert result['success'] is True
        assert result['articles_scraped'] == 2
        assert result['retries'] == 0
        assert result['error'] is None

    @pytest.mark.asyncio
    async def test_execute_scraper_not_implemented(self):
        """Scraper not implemented should be handled"""
        source_config = {'name': 'Unknown Source'}

        with patch('app.services.scheduler_jobs.SCRAPER_REGISTRY', {}):
            result = await execute_scraper_with_retry(
                'Unknown Source',
                source_config
            )

        assert result['success'] is False
        assert result['error'] == 'Scraper not implemented'
        assert result['articles_scraped'] == 0

    @pytest.mark.asyncio
    async def test_execute_scraper_retry_on_failure(self):
        """Failed scrape should retry with backoff"""
        source_config = {'name': 'Test Source'}

        attempt_count = 0

        async def failing_then_success():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                raise Exception("Temporary failure")
            return [Mock(title="Article")]

        mock_scraper = AsyncMock()
        mock_scraper.scrape = failing_then_success

        mock_scraper_class = Mock(return_value=mock_scraper)
        mock_scraper_class.__aenter__ = AsyncMock(return_value=mock_scraper)
        mock_scraper_class.__aexit__ = AsyncMock()

        mock_db = Mock()
        mock_db.add = Mock()
        mock_db.commit = Mock()

        with patch('app.services.scheduler_jobs.SCRAPER_REGISTRY', {'Test Source': mock_scraper_class}):
            with patch('app.services.scheduler_jobs.get_db', return_value=mock_db):
                result = await execute_scraper_with_retry(
                    'Test Source',
                    source_config,
                    tier='medium'
                )

        assert result['success'] is True
        assert result['retries'] == 1  # One retry before success
        assert attempt_count == 2

    @pytest.mark.asyncio
    async def test_execute_scraper_max_retries_exhausted(self):
        """Max retries should be respected"""
        source_config = {'name': 'Test Source'}

        async def always_fails():
            raise Exception("Persistent failure")

        mock_scraper = AsyncMock()
        mock_scraper.scrape = always_fails

        mock_scraper_class = Mock(return_value=mock_scraper)
        mock_scraper_class.__aenter__ = AsyncMock(return_value=mock_scraper)
        mock_scraper_class.__aexit__ = AsyncMock()

        with patch('app.services.scheduler_jobs.SCRAPER_REGISTRY', {'Test Source': mock_scraper_class}):
            with patch('app.services.scheduler_jobs.get_db', return_value=Mock()):
                result = await execute_scraper_with_retry(
                    'Test Source',
                    source_config,
                    tier='low'  # Low tier has fewer retries
                )

        assert result['success'] is False
        assert result['error'] is not None
        assert result['retries'] == SCRAPER_TIERS['low']['max_retries']

    @pytest.mark.asyncio
    async def test_execute_scraper_tier_configuration(self):
        """Different tiers should have different retry counts"""
        source_config = {'name': 'Test Source'}

        async def always_fails():
            raise Exception("Error")

        mock_scraper = AsyncMock()
        mock_scraper.scrape = always_fails
        mock_scraper_class = Mock(return_value=mock_scraper)
        mock_scraper_class.__aenter__ = AsyncMock(return_value=mock_scraper)
        mock_scraper_class.__aexit__ = AsyncMock()

        results = {}

        with patch('app.services.scheduler_jobs.SCRAPER_REGISTRY', {'Test Source': mock_scraper_class}):
            with patch('app.services.scheduler_jobs.get_db', return_value=Mock()):
                for tier in ['high', 'medium', 'low']:
                    result = await execute_scraper_with_retry(
                        'Test Source',
                        source_config,
                        tier=tier
                    )
                    results[tier] = result

        # High tier should have most retries
        assert results['high']['retries'] >= results['medium']['retries']
        assert results['medium']['retries'] >= results['low']['retries']


class TestJobTracking:
    """Test job execution tracking"""

    def setup_method(self):
        """Clear tracking before each test"""
        _job_executions.clear()
        _job_failures.clear()

    def test_track_execution_stores_result(self):
        """Track execution should store job result"""
        result = {
            'job_id': 'test_job',
            'success': True,
            'articles_scraped': 5
        }

        _track_execution('test_job', result)

        assert 'test_job' in _job_executions
        assert len(_job_executions['test_job']) == 1
        assert _job_executions['test_job'][0]['articles_scraped'] == 5

    def test_track_execution_limits_history(self):
        """Track execution should limit history to 100 entries"""
        for i in range(150):
            result = {
                'job_id': f'job_{i}',
                'success': True
            }
            _track_execution('test_job', result)

        # Should only keep last 100
        assert len(_job_executions['test_job']) == 100

    def test_track_execution_resets_failure_count_on_success(self):
        """Successful execution should reset failure count"""
        _job_failures['test_job'] = 5

        result = {
            'job_id': 'test_job',
            'success': True
        }

        _track_execution('test_job', result)

        assert _job_failures['test_job'] == 0

    def test_track_failure_increments_count(self):
        """Track failure should increment failure count"""
        _track_failure('test_job')
        assert _job_failures['test_job'] == 1

        _track_failure('test_job')
        assert _job_failures['test_job'] == 2

    def test_get_job_status_no_executions(self):
        """Get status for job with no executions"""
        status = get_job_status('unknown_job')

        assert status['status'] == 'no_executions'
        assert status['consecutive_failures'] == 0

    def test_get_job_status_with_executions(self):
        """Get status for job with execution history"""
        for i in range(10):
            result = {
                'job_id': 'test_job',
                'success': i % 2 == 0  # Alternate success/failure
            }
            _track_execution('test_job', result)

        status = get_job_status('test_job')

        assert status['total_executions'] == 10
        assert 'success_rate' in status
        assert 'last_execution' in status

    def test_get_job_status_all_jobs(self):
        """Get status for all jobs"""
        for job_id in ['job1', 'job2', 'job3']:
            _track_execution(job_id, {'success': True})

        status = get_job_status()

        assert status['total_jobs'] == 3
        assert 'jobs' in status
        assert len(status['jobs']) == 3


class TestSchedulerMetrics:
    """Test scheduler metrics collection"""

    def setup_method(self):
        """Clear metrics before each test"""
        _job_executions.clear()
        _job_failures.clear()

    def test_get_scheduler_metrics_empty(self):
        """Metrics for empty scheduler"""
        metrics = get_scheduler_metrics()

        assert metrics['total_jobs'] == 0
        assert metrics['total_executions'] == 0
        assert metrics['total_successes'] == 0
        assert metrics['total_failures'] == 0

    def test_get_scheduler_metrics_with_data(self):
        """Metrics with execution data"""
        # Add successful executions
        for i in range(5):
            _track_execution('job1', {'success': True})

        # Add failed executions
        for i in range(3):
            _track_execution('job2', {'success': False})
        _job_failures['job2'] = 3

        metrics = get_scheduler_metrics()

        assert metrics['total_jobs'] == 2
        assert metrics['total_executions'] == 8
        assert metrics['total_successes'] == 5
        assert metrics['total_failures'] == 3
        assert metrics['success_rate'] == 5/8
        assert len(metrics['active_failures']) == 1

    def test_get_scheduler_metrics_success_rate(self):
        """Success rate calculation"""
        # 7 success, 3 failures
        for i in range(10):
            _track_execution('test_job', {'success': i < 7})

        metrics = get_scheduler_metrics()

        assert metrics['success_rate'] == 0.7


class TestManualScraping:
    """Test manual scrape triggering"""

    @pytest.mark.asyncio
    async def test_trigger_manual_scrape_success(self):
        """Manual scrape trigger should work"""
        # Mock sources
        mock_source = {
            'name': 'El Tiempo',
            'url': 'http://example.com'
        }

        mock_scraper = AsyncMock()
        mock_scraper.scrape = AsyncMock(return_value=[Mock()])
        mock_scraper_class = Mock(return_value=mock_scraper)
        mock_scraper_class.__aenter__ = AsyncMock(return_value=mock_scraper)
        mock_scraper_class.__aexit__ = AsyncMock()

        with patch('app.services.scheduler_jobs.get_sources_by_priority', return_value=[mock_source]):
            with patch('app.services.scheduler_jobs.SCRAPER_REGISTRY', {'El Tiempo': mock_scraper_class}):
                with patch('app.services.scheduler_jobs.get_db', return_value=Mock()):
                    result = await trigger_manual_scrape('El Tiempo')

        assert result['success'] is True

    @pytest.mark.asyncio
    async def test_trigger_manual_scrape_not_found(self):
        """Manual scrape for unknown source should fail gracefully"""
        with patch('app.services.scheduler_jobs.get_sources_by_priority', return_value=[]):
            result = await trigger_manual_scrape('Unknown Source')

        assert result['success'] is False
        assert 'not found' in result['error']


class TestCleanupOperations:
    """Test cleanup of old execution records"""

    @pytest.mark.asyncio
    async def test_cleanup_old_executions(self):
        """Old execution records should be removed"""
        from app.config.scheduler_config import SCHEDULER_TIMEZONE

        # Add old executions (25 hours ago)
        old_time = (datetime.now(SCHEDULER_TIMEZONE) - timedelta(hours=25)).isoformat()
        for i in range(5):
            _track_execution('test_job', {
                'success': True,
                'start_time': old_time
            })

        # Add recent executions
        recent_time = datetime.now(SCHEDULER_TIMEZONE).isoformat()
        for i in range(3):
            _track_execution('test_job', {
                'success': True,
                'start_time': recent_time
            })

        await cleanup_old_executions()

        # Only recent executions should remain (assuming 24h retention)
        assert len(_job_executions['test_job']) == 3


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def setup_method(self):
        """Clear state before each test"""
        _job_executions.clear()
        _job_failures.clear()

    @pytest.mark.asyncio
    async def test_concurrent_job_executions(self):
        """Multiple concurrent job executions should be handled"""
        source_config = {'name': 'Test Source'}

        mock_scraper = AsyncMock()
        mock_scraper.scrape = AsyncMock(return_value=[Mock()])
        mock_scraper_class = Mock(return_value=mock_scraper)
        mock_scraper_class.__aenter__ = AsyncMock(return_value=mock_scraper)
        mock_scraper_class.__aexit__ = AsyncMock()

        with patch('app.services.scheduler_jobs.SCRAPER_REGISTRY', {'Test Source': mock_scraper_class}):
            with patch('app.services.scheduler_jobs.get_db', return_value=Mock()):
                tasks = [
                    execute_scraper_with_retry('Test Source', source_config)
                    for _ in range(5)
                ]

                results = await asyncio.gather(*tasks)

        assert len(results) == 5
        assert all(r['success'] for r in results)

    def test_backoff_delay_zero_attempt(self):
        """Backoff for attempt 0 should be minimal"""
        delay = calculate_backoff_delay(0)

        # Should be close to initial delay
        assert delay >= 0
        assert delay <= RETRY_CONFIG['initial_delay'] * 1.5

    def test_job_tracking_thread_safety(self):
        """Job tracking should handle concurrent updates"""
        import threading

        def track_multiple():
            for i in range(100):
                _track_execution('concurrent_job', {'success': True})

        threads = [threading.Thread(target=track_multiple) for _ in range(5)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # All executions should be tracked (up to 100 limit per job)
        assert len(_job_executions['concurrent_job']) == 100
