"""
Error Handling Infrastructure

This module provides:
- Custom exception hierarchy
- Error classification (Transient, Recoverable, Critical)
- Retry logic with circuit breaker
- Dead Letter Queue for failed operations
"""

import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, Optional, Type
from functools import wraps

from pydantic import BaseModel

from app.core.logging_config import get_logger


logger = get_logger(__name__)


# ============================================================================
# Error Classification
# ============================================================================

class ErrorSeverity(str, Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorType(str, Enum):
    """Error types for classification"""
    TRANSIENT = "transient"  # Temporary, retry immediately
    RECOVERABLE = "recoverable"  # Retry with backoff
    PERMANENT = "permanent"  # Don't retry
    UNKNOWN = "unknown"  # Unknown, use default strategy


# ============================================================================
# Custom Exceptions
# ============================================================================

class BaseApplicationError(Exception):
    """Base exception for all application errors"""

    def __init__(
        self,
        message: str,
        error_type: ErrorType = ErrorType.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Dict[str, Any] | None = None
    ):
        self.message = message
        self.error_type = error_type
        self.severity = severity
        self.details = details or {}
        super().__init__(message)


class TransientError(BaseApplicationError):
    """Temporary error that should be retried immediately"""

    def __init__(self, message: str, details: Dict[str, Any] | None = None):
        super().__init__(
            message=message,
            error_type=ErrorType.TRANSIENT,
            severity=ErrorSeverity.LOW,
            details=details
        )


class RecoverableError(BaseApplicationError):
    """Error that can be recovered with retry and backoff"""

    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM, details: Dict[str, Any] | None = None):
        super().__init__(
            message=message,
            error_type=ErrorType.RECOVERABLE,
            severity=severity,
            details=details
        )


class PermanentError(BaseApplicationError):
    """Permanent error that should not be retried"""

    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.HIGH, details: Dict[str, Any] | None = None):
        super().__init__(
            message=message,
            error_type=ErrorType.PERMANENT,
            severity=severity,
            details=details
        )


# Domain-specific errors

class DatabaseError(RecoverableError):
    """Database operation error"""
    pass


class NetworkError(RecoverableError):
    """Network communication error"""
    pass


class ValidationError(PermanentError):
    """Data validation error"""
    pass


class AuthenticationError(PermanentError):
    """Authentication error"""
    pass


class RateLimitError(TransientError):
    """Rate limit exceeded error"""
    pass


class ScraperError(RecoverableError):
    """Web scraping error"""
    pass


class NLPProcessingError(RecoverableError):
    """NLP processing error"""
    pass


# ============================================================================
# Circuit Breaker
# ============================================================================

class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered


class CircuitBreaker:
    """
    Circuit breaker pattern implementation

    Prevents cascading failures by stopping requests to failing services.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Type[Exception] = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED

    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise RecoverableError(
                    "Circuit breaker is OPEN",
                    details={
                        "failure_count": self.failure_count,
                        "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None
                    }
                )

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result

        except self.expected_exception as e:
            self._on_failure()
            raise

    async def call_async(self, func: Callable, *args, **kwargs):
        """Execute async function with circuit breaker protection"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise RecoverableError(
                    "Circuit breaker is OPEN",
                    details={
                        "failure_count": self.failure_count,
                        "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None
                    }
                )

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result

        except self.expected_exception as e:
            self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if not self.last_failure_time:
            return False

        return (datetime.utcnow() - self.last_failure_time).seconds >= self.recovery_timeout

    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(
                "circuit_breaker_opened",
                failure_count=self.failure_count,
                threshold=self.failure_threshold
            )


# ============================================================================
# Retry Logic
# ============================================================================

class RetryConfig(BaseModel):
    """Retry configuration"""
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True


async def retry_with_backoff(
    func: Callable,
    config: RetryConfig = RetryConfig(),
    error_types: tuple[Type[Exception], ...] = (RecoverableError, TransientError),
    *args,
    **kwargs
) -> Any:
    """
    Retry function with exponential backoff

    Args:
        func: Async function to retry
        config: Retry configuration
        error_types: Exception types to retry on
        *args: Function arguments
        **kwargs: Function keyword arguments

    Returns:
        Function result

    Raises:
        Last exception if all retries exhausted
    """
    last_exception = None
    delay = config.initial_delay

    for attempt in range(config.max_attempts):
        try:
            return await func(*args, **kwargs)

        except error_types as e:
            last_exception = e

            if attempt == config.max_attempts - 1:
                logger.error(
                    "retry_exhausted",
                    attempts=config.max_attempts,
                    error=str(e)
                )
                break

            # Calculate delay with exponential backoff
            delay = min(
                config.initial_delay * (config.exponential_base ** attempt),
                config.max_delay
            )

            # Add jitter
            if config.jitter:
                import random
                delay = delay * (0.5 + random.random() * 0.5)

            logger.warning(
                "retry_attempt",
                attempt=attempt + 1,
                max_attempts=config.max_attempts,
                delay=delay,
                error=str(e)
            )

            await asyncio.sleep(delay)

    raise last_exception


def with_retry(config: RetryConfig = RetryConfig()):
    """Decorator for retry with backoff"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_with_backoff(func, config, *args, **kwargs)
        return wrapper
    return decorator


# ============================================================================
# Dead Letter Queue
# ============================================================================

class FailedOperation(BaseModel):
    """Failed operation for DLQ"""
    operation_id: str
    operation_type: str
    payload: Dict[str, Any]
    error_message: str
    error_type: str
    timestamp: datetime
    retry_count: int
    max_retries: int


class DeadLetterQueue:
    """
    Dead Letter Queue for failed operations

    Stores operations that have failed after all retries.
    """

    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.queue: list[FailedOperation] = []

    async def add(self, operation: FailedOperation):
        """Add failed operation to DLQ"""
        self.queue.append(operation)

        # Trim if exceeds max size
        if len(self.queue) > self.max_size:
            self.queue = self.queue[-self.max_size:]

        logger.error(
            "operation_added_to_dlq",
            operation_id=operation.operation_id,
            operation_type=operation.operation_type,
            error_type=operation.error_type,
            retry_count=operation.retry_count
        )

    async def get_failed_operations(
        self,
        operation_type: Optional[str] = None,
        limit: int = 100
    ) -> list[FailedOperation]:
        """Get failed operations from DLQ"""
        operations = self.queue

        if operation_type:
            operations = [op for op in operations if op.operation_type == operation_type]

        return operations[-limit:]

    async def clear(self):
        """Clear the DLQ"""
        count = len(self.queue)
        self.queue.clear()

        logger.info("dlq_cleared", count=count)


# Global DLQ instance
dlq = DeadLetterQueue()
