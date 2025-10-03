"""
APScheduler Job Definitions
All scheduled scraper jobs with retry logic and monitoring
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging
import asyncio
import random

from app.config.scheduler_config import (
    SCRAPER_TIERS, RETRY_CONFIG, RATE_LIMIT_CONFIG,
    SCHEDULER_TIMEZONE, MONITORING_CONFIG
)
from scrapers.sources.strategic_sources import STRATEGIC_SOURCES, get_sources_by_priority
from app.database.connection import get_db
from app.api.scraping import SCRAPER_REGISTRY, run_scraper

logger = logging.getLogger(__name__)


# Job execution tracking
_job_executions: Dict[str, List[Dict[str, Any]]] = {}
_job_failures: Dict[str, int] = {}


async def execute_scraper_with_retry(
    source_name: str,
    source_config: Dict[str, Any],
    tier: str = 'medium'
) -> Dict[str, Any]:
    """
    Execute scraper with exponential backoff retry logic

    Args:
        source_name: Name of the source to scrape
        source_config: Source configuration dictionary
        tier: Priority tier (high/medium/low)

    Returns:
        Execution result dictionary
    """
    job_id = f"scraper_{source_name.lower().replace(' ', '_')}"
    start_time = datetime.now(SCHEDULER_TIMEZONE)

    tier_config = SCRAPER_TIERS.get(tier, SCRAPER_TIERS['medium'])
    max_retries = tier_config['max_retries']

    result = {
        'job_id': job_id,
        'source': source_name,
        'tier': tier,
        'start_time': start_time.isoformat(),
        'success': False,
        'articles_scraped': 0,
        'retries': 0,
        'error': None
    }

    # Check if scraper is implemented
    scraper_class = SCRAPER_REGISTRY.get(source_name)
    if not scraper_class:
        logger.warning(f"Scraper not implemented for {source_name}")
        result['error'] = 'Scraper not implemented'
        _track_execution(job_id, result)
        return result

    # Retry loop with exponential backoff
    for attempt in range(max_retries + 1):
        try:
            # Rate limiting delay
            if attempt > 0:
                delay = calculate_backoff_delay(attempt)
                logger.info(f"Retry {attempt}/{max_retries} for {source_name} after {delay}s")
                await asyncio.sleep(delay)

            # Execute scraper
            logger.info(f"Executing scraper for {source_name} (attempt {attempt + 1})")

            # Get database session
            with get_db() as db:
                async with scraper_class(source_config) as scraper:
                    articles = await scraper.scrape()

                    # Save to database
                    for article in articles:
                        db.add(article)

                    db.commit()

                    result['success'] = True
                    result['articles_scraped'] = len(articles)
                    result['retries'] = attempt

                    logger.info(f"Successfully scraped {len(articles)} articles from {source_name}")
                    break

        except Exception as e:
            result['retries'] = attempt
            result['error'] = str(e)
            logger.error(f"Scraper error for {source_name} (attempt {attempt + 1}): {str(e)}")

            if attempt == max_retries:
                logger.error(f"Max retries reached for {source_name}")
                _track_failure(job_id)

    # Track execution
    end_time = datetime.now(SCHEDULER_TIMEZONE)
    result['end_time'] = end_time.isoformat()
    result['duration_seconds'] = (end_time - start_time).total_seconds()

    _track_execution(job_id, result)

    return result


def calculate_backoff_delay(attempt: int) -> float:
    """
    Calculate exponential backoff delay with jitter

    Args:
        attempt: Retry attempt number (1-indexed)

    Returns:
        Delay in seconds
    """
    base_delay = RETRY_CONFIG['initial_delay']
    max_delay = RETRY_CONFIG['max_delay']
    exponential_base = RETRY_CONFIG['exponential_base']

    # Exponential backoff: delay = base * (2 ^ attempt)
    delay = min(base_delay * (exponential_base ** (attempt - 1)), max_delay)

    # Add jitter to prevent thundering herd
    if RETRY_CONFIG['jitter']:
        jitter = random.uniform(0, delay * 0.1)  # Up to 10% jitter
        delay += jitter

    return delay


def _track_execution(job_id: str, result: Dict[str, Any]) -> None:
    """Track job execution for monitoring"""
    if job_id not in _job_executions:
        _job_executions[job_id] = []

    _job_executions[job_id].append(result)

    # Keep only recent executions (last 100)
    if len(_job_executions[job_id]) > 100:
        _job_executions[job_id] = _job_executions[job_id][-100:]

    # Reset failure count on success
    if result['success']:
        _job_failures[job_id] = 0


def _track_failure(job_id: str) -> None:
    """Track consecutive failures"""
    _job_failures[job_id] = _job_failures.get(job_id, 0) + 1

    # Alert on consecutive failures
    if _job_failures[job_id] >= MONITORING_CONFIG['alert_on_failure_count']:
        logger.critical(
            f"Job {job_id} has failed {_job_failures[job_id]} consecutive times"
        )


async def setup_scraper_jobs(scheduler: AsyncIOScheduler) -> None:
    """
    Set up all scraper jobs based on priority tiers

    Args:
        scheduler: APScheduler instance
    """
    logger.info("Setting up scraper jobs...")

    jobs_added = 0

    # Iterate through priority tiers
    for tier, tier_config in SCRAPER_TIERS.items():
        interval_minutes = tier_config['interval_minutes']

        # Get sources for this tier
        sources = get_sources_by_priority(tier)

        for source in sources:
            source_name = source['name']

            # Create job ID
            job_id = f"scraper_{source_name.lower().replace(' ', '_')}"

            # Add job to scheduler
            scheduler.add_job(
                execute_scraper_with_retry,
                'interval',
                minutes=interval_minutes,
                args=[source_name, source, tier],
                id=job_id,
                name=f"Scrape {source_name}",
                replace_existing=True,
                next_run_time=datetime.now(SCHEDULER_TIMEZONE) + timedelta(seconds=random.randint(0, 60))
            )

            jobs_added += 1
            logger.debug(
                f"Added {tier} priority job for {source_name} "
                f"(interval: {interval_minutes} minutes)"
            )

    logger.info(f"Successfully added {jobs_added} scraper jobs across all tiers")


def get_job_status(job_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get execution status for jobs

    Args:
        job_id: Specific job ID or None for all jobs

    Returns:
        Job execution statistics
    """
    if job_id:
        executions = _job_executions.get(job_id, [])
        failures = _job_failures.get(job_id, 0)

        if not executions:
            return {
                'job_id': job_id,
                'status': 'no_executions',
                'consecutive_failures': failures
            }

        recent = executions[-10:]  # Last 10 executions
        success_count = sum(1 for e in recent if e['success'])

        return {
            'job_id': job_id,
            'total_executions': len(executions),
            'recent_executions': recent,
            'success_rate': success_count / len(recent) if recent else 0,
            'consecutive_failures': failures,
            'last_execution': executions[-1] if executions else None
        }
    else:
        # Return summary for all jobs
        return {
            'total_jobs': len(_job_executions),
            'jobs': {
                job_id: get_job_status(job_id)
                for job_id in _job_executions.keys()
            }
        }


def get_scheduler_metrics() -> Dict[str, Any]:
    """
    Get overall scheduler metrics

    Returns:
        Metrics dictionary
    """
    total_executions = sum(len(execs) for execs in _job_executions.values())
    total_successes = sum(
        sum(1 for e in execs if e['success'])
        for execs in _job_executions.values()
    )

    active_failures = {
        job_id: count
        for job_id, count in _job_failures.items()
        if count > 0
    }

    return {
        'total_jobs': len(_job_executions),
        'total_executions': total_executions,
        'total_successes': total_successes,
        'total_failures': total_executions - total_successes,
        'success_rate': total_successes / total_executions if total_executions > 0 else 0,
        'active_failures': active_failures,
        'jobs_with_issues': len(active_failures),
        'timestamp': datetime.now(SCHEDULER_TIMEZONE).isoformat()
    }


async def cleanup_old_executions() -> None:
    """Clean up old execution records"""
    retention_hours = MONITORING_CONFIG['metrics_retention_hours']
    cutoff_time = datetime.now(SCHEDULER_TIMEZONE) - timedelta(hours=retention_hours)

    cleaned_count = 0

    for job_id, executions in _job_executions.items():
        original_count = len(executions)

        # Filter out old executions
        _job_executions[job_id] = [
            e for e in executions
            if datetime.fromisoformat(e['start_time']) > cutoff_time
        ]

        cleaned_count += original_count - len(_job_executions[job_id])

    logger.info(f"Cleaned up {cleaned_count} old execution records")


async def trigger_manual_scrape(source_name: str) -> Dict[str, Any]:
    """
    Manually trigger a scrape for a specific source

    Args:
        source_name: Name of source to scrape

    Returns:
        Execution result
    """
    # Find source configuration
    source_config = None
    tier = 'medium'

    for priority, sources in [
        ('high', get_sources_by_priority('high')),
        ('medium', get_sources_by_priority('medium')),
        ('low', get_sources_by_priority('low'))
    ]:
        for source in sources:
            if source['name'] == source_name:
                source_config = source
                tier = priority
                break
        if source_config:
            break

    if not source_config:
        return {
            'success': False,
            'error': f'Source {source_name} not found'
        }

    # Execute scraper
    return await execute_scraper_with_retry(source_name, source_config, tier)
