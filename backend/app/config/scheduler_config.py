"""
APScheduler Configuration
PostgreSQL-backed job storage with tiered scheduling
"""

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from pytz import timezone
from typing import Dict, Any
import os

from app.config import settings


# Timezone configuration
SCHEDULER_TIMEZONE = timezone('America/Bogota')  # Colombian timezone

# Job store configuration - PostgreSQL for persistence
JOBSTORES: Dict[str, Any] = {
    'default': SQLAlchemyJobStore(
        url=settings.DATABASE_URL_SYNC,
        tablename='apscheduler_jobs'
    )
}

# Executor configuration - Thread pool for I/O bound scraping tasks
EXECUTORS: Dict[str, Any] = {
    'default': ThreadPoolExecutor(max_workers=settings.MAX_CONCURRENT_SCRAPERS),
    'processpool': ProcessPoolExecutor(max_workers=2)  # For CPU-intensive tasks
}

# Job defaults
JOB_DEFAULTS: Dict[str, Any] = {
    'coalesce': True,  # Combine missed runs into one
    'max_instances': 1,  # Prevent concurrent runs of same job
    'misfire_grace_time': 300,  # 5 minutes grace period for missed jobs
    'replace_existing': True  # Replace job on restart
}

# Scraper tier configurations (based on priority)
SCRAPER_TIERS = {
    'high': {
        'interval_minutes': 15,
        'description': 'High-priority sources - scraped every 15 minutes',
        'max_retries': 5
    },
    'medium': {
        'interval_minutes': 30,
        'description': 'Medium-priority sources - scraped every 30 minutes',
        'max_retries': 3
    },
    'low': {
        'interval_minutes': 60,
        'description': 'Low-priority sources - scraped every 60 minutes',
        'max_retries': 2
    }
}

# Retry configuration
RETRY_CONFIG = {
    'max_retries': 3,
    'initial_delay': 60,  # Start with 1 minute
    'max_delay': 3600,  # Max 1 hour
    'exponential_base': 2,  # Exponential backoff multiplier
    'jitter': True  # Add random jitter to prevent thundering herd
}

# Rate limiting per scraper
RATE_LIMIT_CONFIG = {
    'requests_per_minute': settings.SCRAPER_RATE_LIMIT * 60 if hasattr(settings, 'SCRAPER_RATE_LIMIT') else 300,
    'burst_size': 10,  # Allow short bursts
    'cooldown_seconds': 2  # Delay between requests
}

# Scheduler configuration
SCHEDULER_CONFIG = {
    'jobstores': JOBSTORES,
    'executors': EXECUTORS,
    'job_defaults': JOB_DEFAULTS,
    'timezone': SCHEDULER_TIMEZONE
}

# Monitoring configuration
MONITORING_CONFIG = {
    'enable_metrics': True,
    'metrics_retention_hours': 168,  # 7 days
    'alert_on_failure_count': 3,  # Alert after 3 consecutive failures
    'health_check_interval_minutes': 5
}

# Job persistence settings
PERSISTENCE_CONFIG = {
    'enable_job_recovery': True,
    'recovery_grace_period_hours': 24,  # Recover jobs within 24 hours
    'cleanup_old_jobs_days': 30  # Clean up completed jobs after 30 days
}
