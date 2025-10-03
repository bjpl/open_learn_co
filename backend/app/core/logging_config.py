"""
Structured Logging Configuration with Context Injection

This module configures structlog for JSON-formatted logging with:
- Multi-level logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Context injection (trace_id, user_id, environment)
- Log rotation with retention policies
- Request correlation tracking
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Any, Dict

import structlog
from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields"""

    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        super().add_fields(log_record, record, message_dict)

        # Add timestamp in ISO format
        if not log_record.get('timestamp'):
            log_record['timestamp'] = record.created

        # Add log level
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname

        # Add logger name
        log_record['logger'] = record.name

        # Add module and function info
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno


def add_app_context(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add application context to log events"""
    # Add service name
    event_dict['service'] = 'openlearn-api'

    # Add environment
    import os
    event_dict['environment'] = os.getenv('ENVIRONMENT', 'development')

    return event_dict


def add_trace_context(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add trace context from async context"""
    from contextvars import ContextVar

    # Get trace_id from context
    trace_id: ContextVar[str] = ContextVar('trace_id', default=None)
    if trace_id.get():
        event_dict['trace_id'] = trace_id.get()

    # Get user_id from context
    user_id: ContextVar[str] = ContextVar('user_id', default=None)
    if user_id.get():
        event_dict['user_id'] = user_id.get()

    return event_dict


def configure_logging(
    log_level: str = "INFO",
    log_dir: Path | None = None,
    enable_console: bool = True,
    enable_file: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """
    Configure structured logging with JSON output

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
        enable_console: Enable console logging
        enable_file: Enable file logging
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup files to keep
    """
    # Configure structlog
    structlog.configure(
        processors=[
            # Add context
            add_app_context,
            add_trace_context,
            # Add log level
            structlog.stdlib.add_log_level,
            # Add timestamp
            structlog.processors.TimeStamper(fmt="iso"),
            # Add stack info for exceptions
            structlog.processors.StackInfoRenderer(),
            # Format exceptions
            structlog.processors.format_exc_info,
            # Render to JSON
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    handlers = []

    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        ))
        handlers.append(console_handler)

    # File handler with rotation
    if enable_file and log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)

        # Application logs
        app_log_file = log_dir / "app.log"
        app_handler = logging.handlers.RotatingFileHandler(
            app_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        app_handler.setFormatter(CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        ))
        handlers.append(app_handler)

        # Error logs (ERROR and above)
        error_log_file = log_dir / "error.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        ))
        handlers.append(error_handler)

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        handlers=handlers,
        force=True
    )

    # Set levels for noisy libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("selenium").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a configured logger instance

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


# Context variables for request tracking
from contextvars import ContextVar

trace_id_var: ContextVar[str] = ContextVar('trace_id', default=None)
user_id_var: ContextVar[str] = ContextVar('user_id', default=None)
request_id_var: ContextVar[str] = ContextVar('request_id', default=None)


def set_trace_context(trace_id: str, user_id: str | None = None, request_id: str | None = None) -> None:
    """Set trace context for logging"""
    trace_id_var.set(trace_id)
    if user_id:
        user_id_var.set(user_id)
    if request_id:
        request_id_var.set(request_id)


def clear_trace_context() -> None:
    """Clear trace context"""
    trace_id_var.set(None)
    user_id_var.set(None)
    request_id_var.set(None)
