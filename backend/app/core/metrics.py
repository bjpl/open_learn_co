"""
Prometheus Metrics for Monitoring

This module provides:
- Custom metrics for scrapers, API, database, scheduler
- Automatic metric collection
- Prometheus exposition format
"""

from typing import Callable
from functools import wraps
import time

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Summary,
    Info,
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST
)

from app.core.logging_config import get_logger


logger = get_logger(__name__)

# Create custom registry
registry = CollectorRegistry()

# ============================================================================
# API Metrics
# ============================================================================

http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=registry
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0),
    registry=registry
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'Number of HTTP requests in progress',
    ['method', 'endpoint'],
    registry=registry
)

# ============================================================================
# Scraper Metrics
# ============================================================================

scraper_requests_total = Counter(
    'scraper_requests_total',
    'Total scraper requests',
    ['scraper_name', 'status'],
    registry=registry
)

scraper_duration_seconds = Histogram(
    'scraper_duration_seconds',
    'Scraper execution duration in seconds',
    ['scraper_name'],
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
    registry=registry
)

scraper_articles_scraped = Counter(
    'scraper_articles_scraped_total',
    'Total articles scraped',
    ['scraper_name', 'source'],
    registry=registry
)

scraper_errors_total = Counter(
    'scraper_errors_total',
    'Total scraper errors',
    ['scraper_name', 'error_type'],
    registry=registry
)

scraper_active = Gauge(
    'scraper_active_tasks',
    'Number of active scraper tasks',
    ['scraper_name'],
    registry=registry
)

# ============================================================================
# Database Metrics
# ============================================================================

db_connections_active = Gauge(
    'db_connections_active',
    'Number of active database connections',
    ['pool_name'],
    registry=registry
)

db_connections_total = Counter(
    'db_connections_total',
    'Total database connections created',
    ['pool_name'],
    registry=registry
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation', 'table'],
    buckets=(0.001, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0),
    registry=registry
)

db_query_errors_total = Counter(
    'db_query_errors_total',
    'Total database query errors',
    ['operation', 'error_type'],
    registry=registry
)

# ============================================================================
# NLP Processing Metrics
# ============================================================================

nlp_processing_duration_seconds = Histogram(
    'nlp_processing_duration_seconds',
    'NLP processing duration in seconds',
    ['operation', 'model'],
    buckets=(0.01, 0.1, 0.5, 1.0, 5.0, 10.0),
    registry=registry
)

nlp_documents_processed = Counter(
    'nlp_documents_processed_total',
    'Total documents processed by NLP',
    ['operation', 'language'],
    registry=registry
)

# ============================================================================
# Task Queue Metrics
# ============================================================================

task_queue_length = Gauge(
    'task_queue_length',
    'Number of tasks in queue',
    ['queue_name'],
    registry=registry
)

task_execution_duration_seconds = Histogram(
    'task_execution_duration_seconds',
    'Task execution duration in seconds',
    ['task_name', 'status'],
    buckets=(0.1, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0),
    registry=registry
)

task_retries_total = Counter(
    'task_retries_total',
    'Total task retries',
    ['task_name'],
    registry=registry
)

# ============================================================================
# System Metrics
# ============================================================================

system_info = Info(
    'system_info',
    'System information',
    registry=registry
)

application_version = Info(
    'application_version',
    'Application version information',
    registry=registry
)

# ============================================================================
# Metric Decorators
# ============================================================================

def track_request_metrics(endpoint: str):
    """Decorator to track HTTP request metrics"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            method = kwargs.get('request', args[0] if args else None).method

            http_requests_in_progress.labels(
                method=method,
                endpoint=endpoint
            ).inc()

            start_time = time.time()
            status = 500

            try:
                response = await func(*args, **kwargs)
                status = getattr(response, 'status_code', 200)
                return response

            except Exception as e:
                logger.error(f"Request failed: {e}")
                raise

            finally:
                duration = time.time() - start_time

                http_request_duration_seconds.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(duration)

                http_requests_total.labels(
                    method=method,
                    endpoint=endpoint,
                    status=status
                ).inc()

                http_requests_in_progress.labels(
                    method=method,
                    endpoint=endpoint
                ).dec()

        return wrapper
    return decorator


def track_scraper_metrics(scraper_name: str):
    """Decorator to track scraper metrics"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            scraper_active.labels(scraper_name=scraper_name).inc()

            start_time = time.time()
            status = "success"

            try:
                result = await func(*args, **kwargs)
                return result

            except Exception as e:
                status = "error"
                error_type = type(e).__name__

                scraper_errors_total.labels(
                    scraper_name=scraper_name,
                    error_type=error_type
                ).inc()

                raise

            finally:
                duration = time.time() - start_time

                scraper_duration_seconds.labels(
                    scraper_name=scraper_name
                ).observe(duration)

                scraper_requests_total.labels(
                    scraper_name=scraper_name,
                    status=status
                ).inc()

                scraper_active.labels(scraper_name=scraper_name).dec()

        return wrapper
    return decorator


def track_db_query(operation: str, table: str):
    """Decorator to track database query metrics"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                return result

            except Exception as e:
                error_type = type(e).__name__

                db_query_errors_total.labels(
                    operation=operation,
                    error_type=error_type
                ).inc()

                raise

            finally:
                duration = time.time() - start_time

                db_query_duration_seconds.labels(
                    operation=operation,
                    table=table
                ).observe(duration)

        return wrapper
    return decorator


def track_nlp_processing(operation: str, model: str):
    """Decorator to track NLP processing metrics"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)

                # Increment processed documents
                language = kwargs.get('language', 'unknown')
                nlp_documents_processed.labels(
                    operation=operation,
                    language=language
                ).inc()

                return result

            finally:
                duration = time.time() - start_time

                nlp_processing_duration_seconds.labels(
                    operation=operation,
                    model=model
                ).observe(duration)

        return wrapper
    return decorator


def set_system_info(version: str, environment: str, python_version: str):
    """Set system information metrics"""
    system_info.info({
        'environment': environment,
        'python_version': python_version
    })

    application_version.info({
        'version': version
    })


def get_metrics() -> bytes:
    """Get Prometheus metrics in exposition format"""
    return generate_latest(registry)


def get_content_type() -> str:
    """Get Prometheus metrics content type"""
    return CONTENT_TYPE_LATEST
