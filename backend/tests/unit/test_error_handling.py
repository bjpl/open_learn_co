"""
Comprehensive Error Handling Tests

Tests for:
- Custom exception hierarchy
- Circuit breaker pattern
- Retry logic with exponential backoff
- Dead Letter Queue (DLQ)
- Error classification and severity
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from app.core.error_handling import (
    ErrorSeverity,
    ErrorType,
    BaseApplicationError,
    TransientError,
    RecoverableError,
    PermanentError,
    DatabaseError,
    NetworkError,
    ValidationError,
    AuthenticationError,
    RateLimitError,
    ScraperError,
    NLPProcessingError,
    CircuitBreaker,
    CircuitState,
    RetryConfig,
    retry_with_backoff,
    with_retry,
    FailedOperation,
    DeadLetterQueue,
    dlq,
)


class TestCustomExceptions:
    """Test custom exception hierarchy"""

    def test_base_application_error_creation(self):
        """BaseApplicationError should store all attributes"""
        error = BaseApplicationError(
            message="Test error",
            error_type=ErrorType.RECOVERABLE,
            severity=ErrorSeverity.HIGH,
            details={"code": 500, "context": "test"}
        )

        assert error.message == "Test error"
        assert error.error_type == ErrorType.RECOVERABLE
        assert error.severity == ErrorSeverity.HIGH
        assert error.details["code"] == 500
        assert error.details["context"] == "test"

    def test_transient_error_defaults(self):
        """TransientError should have correct defaults"""
        error = TransientError("Temporary issue")

        assert error.error_type == ErrorType.TRANSIENT
        assert error.severity == ErrorSeverity.LOW
        assert error.message == "Temporary issue"

    def test_recoverable_error_defaults(self):
        """RecoverableError should have correct defaults"""
        error = RecoverableError("Recoverable issue")

        assert error.error_type == ErrorType.RECOVERABLE
        assert error.severity == ErrorSeverity.MEDIUM

    def test_permanent_error_defaults(self):
        """PermanentError should have correct defaults"""
        error = PermanentError("Permanent issue")

        assert error.error_type == ErrorType.PERMANENT
        assert error.severity == ErrorSeverity.HIGH

    def test_database_error_is_recoverable(self):
        """DatabaseError should be recoverable"""
        error = DatabaseError("Connection failed")

        assert error.error_type == ErrorType.RECOVERABLE
        assert isinstance(error, RecoverableError)

    def test_network_error_is_recoverable(self):
        """NetworkError should be recoverable"""
        error = NetworkError("Timeout")

        assert error.error_type == ErrorType.RECOVERABLE

    def test_validation_error_is_permanent(self):
        """ValidationError should be permanent"""
        error = ValidationError("Invalid input")

        assert error.error_type == ErrorType.PERMANENT

    def test_authentication_error_is_permanent(self):
        """AuthenticationError should be permanent"""
        error = AuthenticationError("Invalid credentials")

        assert error.error_type == ErrorType.PERMANENT

    def test_rate_limit_error_is_transient(self):
        """RateLimitError should be transient"""
        error = RateLimitError("Too many requests")

        assert error.error_type == ErrorType.TRANSIENT

    def test_exception_with_details(self):
        """Exceptions should store details"""
        error = NetworkError(
            "Connection timeout",
            details={"timeout": 30, "url": "http://example.com"}
        )

        assert error.details["timeout"] == 30
        assert error.details["url"] == "http://example.com"


class TestCircuitBreaker:
    """Test circuit breaker pattern"""

    def test_circuit_breaker_initial_state(self):
        """Circuit breaker should start in closed state"""
        cb = CircuitBreaker(failure_threshold=3)

        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_circuit_breaker_success(self):
        """Successful calls should keep circuit closed"""
        cb = CircuitBreaker(failure_threshold=3)

        def successful_func():
            return "success"

        result = cb.call(successful_func)

        assert result == "success"
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_circuit_breaker_opens_after_threshold(self):
        """Circuit should open after failure threshold"""
        cb = CircuitBreaker(failure_threshold=3, expected_exception=ValueError)

        def failing_func():
            raise ValueError("Error")

        # Fail 3 times
        for _ in range(3):
            with pytest.raises(ValueError):
                cb.call(failing_func)

        assert cb.state == CircuitState.OPEN
        assert cb.failure_count == 3

    def test_circuit_breaker_rejects_when_open(self):
        """Open circuit should reject calls"""
        cb = CircuitBreaker(failure_threshold=2, expected_exception=ValueError)

        def failing_func():
            raise ValueError("Error")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                cb.call(failing_func)

        assert cb.state == CircuitState.OPEN

        # Next call should be rejected
        with pytest.raises(RecoverableError) as exc:
            cb.call(failing_func)

        assert "Circuit breaker is OPEN" in str(exc.value)

    def test_circuit_breaker_half_open_after_timeout(self):
        """Circuit should enter half-open after recovery timeout"""
        cb = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=1,  # 1 second
            expected_exception=ValueError
        )

        def failing_func():
            raise ValueError("Error")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                cb.call(failing_func)

        assert cb.state == CircuitState.OPEN

        # Wait for recovery timeout
        import time
        time.sleep(1.1)

        # Should attempt reset (will fail and go back to open)
        with pytest.raises(ValueError):
            cb.call(failing_func)

        # State should have been half-open during attempt
        # (but back to open after failure)

    @pytest.mark.asyncio
    async def test_circuit_breaker_async_success(self):
        """Async circuit breaker should handle successful calls"""
        cb = CircuitBreaker(failure_threshold=3)

        async def successful_async_func():
            await asyncio.sleep(0.01)
            return "success"

        result = await cb.call_async(successful_async_func)

        assert result == "success"
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_breaker_async_failure(self):
        """Async circuit breaker should handle failures"""
        cb = CircuitBreaker(failure_threshold=2, expected_exception=ValueError)

        async def failing_async_func():
            await asyncio.sleep(0.01)
            raise ValueError("Async error")

        for _ in range(2):
            with pytest.raises(ValueError):
                await cb.call_async(failing_async_func)

        assert cb.state == CircuitState.OPEN

    def test_circuit_breaker_resets_on_success(self):
        """Successful call should reset failure count"""
        cb = CircuitBreaker(failure_threshold=3, expected_exception=ValueError)

        def sometimes_failing_func(should_fail):
            if should_fail:
                raise ValueError("Error")
            return "success"

        # Fail once
        with pytest.raises(ValueError):
            cb.call(sometimes_failing_func, True)

        assert cb.failure_count == 1

        # Succeed
        result = cb.call(sometimes_failing_func, False)

        assert result == "success"
        assert cb.failure_count == 0
        assert cb.state == CircuitState.CLOSED


class TestRetryLogic:
    """Test retry with exponential backoff"""

    @pytest.mark.asyncio
    async def test_retry_succeeds_on_first_attempt(self):
        """Retry should return immediately if first attempt succeeds"""
        async def successful_func():
            return "success"

        config = RetryConfig(max_attempts=3)
        result = await retry_with_backoff(successful_func, config)

        assert result == "success"

    @pytest.mark.asyncio
    async def test_retry_succeeds_after_failures(self):
        """Retry should eventually succeed after transient failures"""
        attempt_count = 0

        async def func_succeeds_on_third():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise TransientError("Temporary failure")
            return "success"

        config = RetryConfig(max_attempts=5, initial_delay=0.01)
        result = await retry_with_backoff(func_succeeds_on_third, config)

        assert result == "success"
        assert attempt_count == 3

    @pytest.mark.asyncio
    async def test_retry_exhausts_attempts(self):
        """Retry should raise last exception after max attempts"""
        async def always_fails():
            raise RecoverableError("Persistent failure")

        config = RetryConfig(max_attempts=3, initial_delay=0.01)

        with pytest.raises(RecoverableError) as exc:
            await retry_with_backoff(always_fails, config)

        assert "Persistent failure" in str(exc.value)

    @pytest.mark.asyncio
    async def test_retry_exponential_backoff(self):
        """Retry delays should increase exponentially"""
        delays = []

        async def failing_func():
            raise RecoverableError("Error")

        config = RetryConfig(
            max_attempts=4,
            initial_delay=0.1,
            exponential_base=2.0,
            jitter=False  # Disable jitter for predictable testing
        )

        start_time = datetime.utcnow()

        with pytest.raises(RecoverableError):
            await retry_with_backoff(failing_func, config)

        total_time = (datetime.utcnow() - start_time).total_seconds()

        # Expected delays: 0.1, 0.2, 0.4 = 0.7 seconds minimum
        assert total_time >= 0.7

    @pytest.mark.asyncio
    async def test_retry_max_delay_cap(self):
        """Retry delays should be capped at max_delay"""
        async def failing_func():
            raise RecoverableError("Error")

        config = RetryConfig(
            max_attempts=5,
            initial_delay=1.0,
            max_delay=2.0,  # Cap at 2 seconds
            exponential_base=2.0,
            jitter=False
        )

        start_time = datetime.utcnow()

        with pytest.raises(RecoverableError):
            await retry_with_backoff(failing_func, config)

        total_time = (datetime.utcnow() - start_time).total_seconds()

        # Even with exponential backoff, should not exceed max_delay per retry
        # Max possible: 2.0 + 2.0 + 2.0 + 2.0 = 8.0 seconds
        assert total_time < 10.0

    @pytest.mark.asyncio
    async def test_retry_with_jitter(self):
        """Retry with jitter should add randomness to delays"""
        async def failing_func():
            raise TransientError("Error")

        config = RetryConfig(
            max_attempts=3,
            initial_delay=0.1,
            jitter=True
        )

        # Run multiple times and collect timings
        timings = []
        for _ in range(3):
            start = datetime.utcnow()
            with pytest.raises(TransientError):
                await retry_with_backoff(failing_func, config)
            timings.append((datetime.utcnow() - start).total_seconds())

        # With jitter, timings should vary
        assert len(set(timings)) > 1 or timings[0] != timings[1]

    @pytest.mark.asyncio
    async def test_retry_decorator(self):
        """@with_retry decorator should work correctly"""
        attempt_count = 0

        @with_retry(RetryConfig(max_attempts=3, initial_delay=0.01))
        async def decorated_func():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                raise RecoverableError("Temporary error")
            return "success"

        result = await decorated_func()

        assert result == "success"
        assert attempt_count == 2

    @pytest.mark.asyncio
    async def test_retry_only_on_specified_error_types(self):
        """Retry should only retry specified error types"""
        async def func_raises_wrong_error():
            raise ValueError("Not a retryable error")

        config = RetryConfig(max_attempts=3)

        # Should not retry ValueError (not in error_types)
        with pytest.raises(ValueError):
            await retry_with_backoff(
                func_raises_wrong_error,
                config,
                error_types=(RecoverableError, TransientError)
            )


class TestDeadLetterQueue:
    """Test Dead Letter Queue functionality"""

    @pytest.mark.asyncio
    async def test_dlq_add_operation(self):
        """DLQ should store failed operations"""
        dlq = DeadLetterQueue(max_size=100)

        operation = FailedOperation(
            operation_id="op_123",
            operation_type="scrape",
            payload={"url": "http://example.com"},
            error_message="Timeout",
            error_type="NetworkError",
            timestamp=datetime.utcnow(),
            retry_count=3,
            max_retries=3
        )

        await dlq.add(operation)

        assert len(dlq.queue) == 1
        assert dlq.queue[0].operation_id == "op_123"

    @pytest.mark.asyncio
    async def test_dlq_max_size_limit(self):
        """DLQ should trim to max size"""
        dlq = DeadLetterQueue(max_size=5)

        # Add 10 operations
        for i in range(10):
            operation = FailedOperation(
                operation_id=f"op_{i}",
                operation_type="test",
                payload={},
                error_message="Error",
                error_type="TestError",
                timestamp=datetime.utcnow(),
                retry_count=1,
                max_retries=3
            )
            await dlq.add(operation)

        # Should only keep last 5
        assert len(dlq.queue) == 5
        assert dlq.queue[0].operation_id == "op_5"
        assert dlq.queue[-1].operation_id == "op_9"

    @pytest.mark.asyncio
    async def test_dlq_get_failed_operations(self):
        """DLQ should retrieve failed operations"""
        dlq = DeadLetterQueue()

        # Add operations
        for i in range(5):
            operation = FailedOperation(
                operation_id=f"op_{i}",
                operation_type="scrape" if i % 2 == 0 else "analyze",
                payload={},
                error_message="Error",
                error_type="TestError",
                timestamp=datetime.utcnow(),
                retry_count=1,
                max_retries=3
            )
            await dlq.add(operation)

        # Get all operations
        all_ops = await dlq.get_failed_operations()
        assert len(all_ops) == 5

        # Get filtered by type
        scrape_ops = await dlq.get_failed_operations(operation_type="scrape")
        assert len(scrape_ops) == 3
        assert all(op.operation_type == "scrape" for op in scrape_ops)

    @pytest.mark.asyncio
    async def test_dlq_get_with_limit(self):
        """DLQ should respect limit parameter"""
        dlq = DeadLetterQueue()

        # Add 10 operations
        for i in range(10):
            operation = FailedOperation(
                operation_id=f"op_{i}",
                operation_type="test",
                payload={},
                error_message="Error",
                error_type="TestError",
                timestamp=datetime.utcnow(),
                retry_count=1,
                max_retries=3
            )
            await dlq.add(operation)

        # Get with limit
        ops = await dlq.get_failed_operations(limit=3)

        assert len(ops) == 3
        # Should return most recent
        assert ops[-1].operation_id == "op_9"

    @pytest.mark.asyncio
    async def test_dlq_clear(self):
        """DLQ clear should remove all operations"""
        dlq = DeadLetterQueue()

        # Add operations
        for i in range(5):
            operation = FailedOperation(
                operation_id=f"op_{i}",
                operation_type="test",
                payload={},
                error_message="Error",
                error_type="TestError",
                timestamp=datetime.utcnow(),
                retry_count=1,
                max_retries=3
            )
            await dlq.add(operation)

        assert len(dlq.queue) == 5

        await dlq.clear()

        assert len(dlq.queue) == 0


class TestErrorHandlingIntegration:
    """Integration tests for error handling components"""

    @pytest.mark.asyncio
    async def test_retry_with_circuit_breaker(self):
        """Retry logic combined with circuit breaker"""
        cb = CircuitBreaker(failure_threshold=3, expected_exception=NetworkError)
        attempt_count = 0

        async def func_with_circuit_breaker():
            nonlocal attempt_count
            attempt_count += 1
            return await cb.call_async(self._failing_network_call)

        async def _failing_network_call():
            raise NetworkError("Connection failed")

        config = RetryConfig(max_attempts=5, initial_delay=0.01)

        with pytest.raises(NetworkError):
            await retry_with_backoff(
                func_with_circuit_breaker,
                config,
                error_types=(NetworkError,)
            )

        # Circuit should be open after threshold
        assert cb.state == CircuitState.OPEN

    @staticmethod
    async def _failing_network_call():
        raise NetworkError("Connection failed")

    @pytest.mark.asyncio
    async def test_error_to_dlq_workflow(self):
        """Failed operations after retry should go to DLQ"""
        dlq = DeadLetterQueue()
        max_retries = 3

        async def failing_operation():
            raise ScraperError("Scraping failed")

        config = RetryConfig(max_attempts=max_retries, initial_delay=0.01)

        try:
            await retry_with_backoff(
                failing_operation,
                config,
                error_types=(ScraperError,)
            )
        except ScraperError as e:
            # Add to DLQ after retry exhaustion
            operation = FailedOperation(
                operation_id="scrape_001",
                operation_type="scrape",
                payload={"url": "http://example.com"},
                error_message=str(e),
                error_type=type(e).__name__,
                timestamp=datetime.utcnow(),
                retry_count=max_retries,
                max_retries=max_retries
            )
            await dlq.add(operation)

        # Verify in DLQ
        ops = await dlq.get_failed_operations()
        assert len(ops) == 1
        assert ops[0].operation_id == "scrape_001"
        assert ops[0].retry_count == max_retries
