"""
Core infrastructure modules

This package contains core infrastructure components:
- logging_config: Structured logging with JSON output
- metrics: Prometheus metrics collection
- error_handling: Exception handling and retry logic
- alerting: Alert management and notifications
- security: JWT authentication and password hashing
"""

from .logging_config import configure_logging, get_logger
from .metrics import (
    http_requests_total,
    scraper_requests_total,
    db_query_duration_seconds,
    track_request_metrics,
    track_scraper_metrics,
    track_db_query,
)
from .error_handling import (
    BaseApplicationError,
    TransientError,
    RecoverableError,
    PermanentError,
    DatabaseError,
    NetworkError,
    ValidationError,
    ScraperError,
    retry_with_backoff,
    with_retry,
)
from .alerting import alert_manager, Alert, AlertSeverity
from .security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    hash_password,
    verify_password,
    get_current_user,
    get_current_active_user,
)

__all__ = [
    # Logging
    "configure_logging",
    "get_logger",
    # Metrics
    "http_requests_total",
    "scraper_requests_total",
    "db_query_duration_seconds",
    "track_request_metrics",
    "track_scraper_metrics",
    "track_db_query",
    # Error Handling
    "BaseApplicationError",
    "TransientError",
    "RecoverableError",
    "PermanentError",
    "DatabaseError",
    "NetworkError",
    "ValidationError",
    "ScraperError",
    "retry_with_backoff",
    "with_retry",
    # Alerting
    "alert_manager",
    "Alert",
    "AlertSeverity",
    # Security
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    "hash_password",
    "verify_password",
    "get_current_user",
    "get_current_active_user",
]
