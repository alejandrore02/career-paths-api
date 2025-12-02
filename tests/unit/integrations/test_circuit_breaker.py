"""Unit tests for circuit breaker pattern implementation.

Tests verify:
- Circuit remains closed during normal operation
- Circuit opens after failure threshold
- Circuit rejects calls when open
- Circuit transitions to half-open after timeout
- Circuit closes after successful recovery
- Failure counter resets appropriately
"""

import time
from unittest.mock import AsyncMock, patch

import pytest

from app.integrations.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    with_circuit_breaker,
)
from app.core.errors import ExternalServiceError
from tests.helpers.async_mocks import (
    CallSequenceMock,
    create_failing_mock,
    create_always_failing_mock,
)


# ============================================================================
# Tests for CircuitBreaker class - CLOSED state
# ============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_circuit_breaker_starts_closed():
    """Circuit should start in CLOSED state."""
    # Arrange
    cb = CircuitBreaker(failure_threshold=3, timeout=60.0, name="test")

    # Assert
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_circuit_breaker_allows_calls_when_closed():
    """Circuit should allow calls in CLOSED state."""
    # Arrange
    cb = CircuitBreaker(failure_threshold=3, timeout=60.0, name="test")
    mock_func = CallSequenceMock([{"data": "success"}])

    # Act
    result = await cb.call(mock_func)

    # Assert
    assert result == {"data": "success"}
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_circuit_breaker_increments_failure_count():
    """Circuit should increment failure count on errors but stay closed below threshold."""
    # Arrange
    cb = CircuitBreaker(failure_threshold=3, timeout=60.0, name="test")
    mock_func = create_always_failing_mock(
        attempts=2,
        exception=ConnectionError("Service unavailable"),
    )

    # Act: first failure
    with pytest.raises(ConnectionError):
        await cb.call(mock_func)

    # Assert: still closed, count incremented
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 1

    # Act: second failure
    with pytest.raises(ConnectionError):
        await cb.call(mock_func)

    # Assert: still closed but approaching threshold
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 2


# ============================================================================
# Tests for CircuitBreaker class - OPEN state
# ============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_threshold():
    """Circuit should open after reaching failure threshold."""
    # Arrange
    failure_threshold = 3
    cb = CircuitBreaker(failure_threshold=failure_threshold, timeout=60.0, name="test")
    mock_func = create_always_failing_mock(
        attempts=failure_threshold,
        exception=TimeoutError("Service timeout"),
    )

    # Act: trigger failures up to threshold
    for _ in range(failure_threshold):
        with pytest.raises(TimeoutError):
            await cb.call(mock_func)

    # Assert: circuit opened
    assert cb.state == CircuitState.OPEN
    assert cb.failure_count == failure_threshold


@pytest.mark.unit
@pytest.mark.asyncio
async def test_circuit_breaker_rejects_calls_when_open():
    """Circuit should reject calls immediately when open."""
    # Arrange
    cb = CircuitBreaker(failure_threshold=2, timeout=60.0, name="test")

    # Trigger failures to open circuit
    failing_func = create_always_failing_mock(
        attempts=2, exception=ValueError("Fail")
    )
    for _ in range(2):
        with pytest.raises(ValueError):
            await cb.call(failing_func)

    assert cb.state == CircuitState.OPEN

    # Act & Assert: new call should be rejected without executing
    success_func = CallSequenceMock([{"data": "would succeed"}])
    with pytest.raises(ExternalServiceError) as exc_info:
        await cb.call(success_func)

    assert "Circuit breaker 'test' is OPEN" in str(exc_info.value)
    assert success_func.call_count == 0, "Function should not be called when circuit is open"


# ============================================================================
# Tests for CircuitBreaker class - HALF_OPEN state
# ============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_circuit_breaker_transitions_to_half_open_after_timeout():
    """Circuit should transition to HALF_OPEN after timeout expires."""
    # Arrange
    timeout = 0.1  # 100ms for fast test
    cb = CircuitBreaker(failure_threshold=2, timeout=timeout, name="test")

    # Open the circuit
    failing_func = create_always_failing_mock(attempts=2, exception=RuntimeError("Fail"))
    for _ in range(2):
        with pytest.raises(RuntimeError):
            await cb.call(failing_func)

    assert cb.state == CircuitState.OPEN

    # Act: advance time past timeout using monkeypatch
    original_time = time.time()
    with patch("time.time", return_value=original_time + timeout + 0.01):
        # Circuit should attempt reset on next call
        success_func = CallSequenceMock([{"data": "success"}])
        result = await cb.call(success_func)

    # Assert: circuit transitioned to HALF_OPEN then CLOSED on success
    assert result == {"data": "success"}
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_circuit_breaker_half_open_closes_on_success():
    """Circuit should close after successful call in HALF_OPEN state."""
    # Arrange
    timeout = 0.05
    cb = CircuitBreaker(failure_threshold=1, timeout=timeout, name="test")

    # Open circuit
    with pytest.raises(ValueError):
        await cb.call(create_always_failing_mock(1, ValueError("Fail")))

    assert cb.state == CircuitState.OPEN

    # Act: wait for timeout and make successful call
    original_time = time.time()
    with patch("time.time", return_value=original_time + timeout + 0.01):
        success_func = CallSequenceMock([{"data": "recovered"}])
        result = await cb.call(success_func)

    # Assert
    assert result == {"data": "recovered"}
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0
    assert cb.last_failure_time is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_circuit_breaker_half_open_reopens_on_failure():
    """Circuit should reopen if call fails in HALF_OPEN state."""
    # Arrange
    timeout = 0.05
    cb = CircuitBreaker(failure_threshold=1, timeout=timeout, name="test")

    # Open circuit
    with pytest.raises(ValueError):
        await cb.call(create_always_failing_mock(1, ValueError("Initial fail")))

    assert cb.state == CircuitState.OPEN

    # Act: wait for timeout, then fail again in HALF_OPEN
    original_time = time.time()
    with patch("time.time", return_value=original_time + timeout + 0.01):
        failing_func = CallSequenceMock([ConnectionError("Still failing")])
        with pytest.raises(ConnectionError):
            await cb.call(failing_func)

    # Assert: circuit reopened
    assert cb.state == CircuitState.OPEN
    assert cb.failure_count == 2  # Incremented again


# ============================================================================
# Tests for @with_circuit_breaker decorator
# ============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_with_circuit_breaker_decorator_allows_success():
    """Decorator should allow successful calls."""

    # Arrange
    @with_circuit_breaker(failure_threshold=3, timeout=60.0, name="decorated_test")
    async def decorated_func() -> str:
        return "success"

    # Act
    result = await decorated_func()

    # Assert
    assert result == "success"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_with_circuit_breaker_decorator_opens_on_failures():
    """Decorator should open circuit after threshold failures."""
    # Arrange
    call_count = 0

    @with_circuit_breaker(failure_threshold=2, timeout=60.0, name="failing_test")
    async def decorated_func() -> None:
        nonlocal call_count
        call_count += 1
        raise ValueError(f"Failure {call_count}")

    # Act: trigger failures
    with pytest.raises(ValueError):
        await decorated_func()
    with pytest.raises(ValueError):
        await decorated_func()

    # Assert: next call should be rejected by open circuit
    with pytest.raises(ExternalServiceError) as exc_info:
        await decorated_func()

    assert "Circuit breaker 'failing_test' is OPEN" in str(exc_info.value)
    assert call_count == 2, "Function should not be called when circuit is open"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_with_circuit_breaker_decorator_preserves_metadata():
    """Decorator should preserve function metadata."""

    # Arrange
    @with_circuit_breaker(failure_threshold=3, timeout=60.0, name="metadata_test")
    async def my_documented_function() -> int:
        """This function has documentation."""
        return 42

    # Assert
    assert my_documented_function.__name__ == "my_documented_function"
    assert my_documented_function.__doc__ is not None
    assert "documentation" in my_documented_function.__doc__


# ============================================================================
# Integration scenarios
# ============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_circuit_breaker_with_mixed_success_and_failures():
    """Circuit should handle mixed success/failure patterns correctly."""
    # Arrange
    cb = CircuitBreaker(failure_threshold=3, timeout=60.0, name="mixed_test")

    # Act & Assert: successful call
    success_func = CallSequenceMock([{"data": "ok"}])
    result = await cb.call(success_func)
    assert result == {"data": "ok"}
    assert cb.failure_count == 0

    # One failure
    with pytest.raises(ValueError):
        await cb.call(create_always_failing_mock(1, ValueError("Fail 1")))
    assert cb.failure_count == 1
    assert cb.state == CircuitState.CLOSED

    # Another success resets? No, failures accumulate until threshold
    await cb.call(CallSequenceMock([{"data": "ok2"}]))
    assert cb.failure_count == 1  # Failures persist (implementation-specific)

    # Two more failures to reach threshold
    with pytest.raises(ValueError):
        await cb.call(create_always_failing_mock(1, ValueError("Fail 2")))
    with pytest.raises(ValueError):
        await cb.call(create_always_failing_mock(1, ValueError("Fail 3")))

    # Circuit should be open now
    assert cb.state == CircuitState.OPEN


@pytest.mark.unit
@pytest.mark.asyncio
async def test_circuit_breaker_recovery_flow():
    """Test full recovery flow: CLOSED -> OPEN -> HALF_OPEN -> CLOSED."""
    # Arrange
    timeout = 0.1
    cb = CircuitBreaker(failure_threshold=2, timeout=timeout, name="recovery_test")

    # Step 1: CLOSED state - trigger failures to open
    failing_func = create_always_failing_mock(2, TimeoutError("Service down"))
    with pytest.raises(TimeoutError):
        await cb.call(failing_func)
    with pytest.raises(TimeoutError):
        await cb.call(failing_func)

    assert cb.state == CircuitState.OPEN

    # Step 2: OPEN state - reject calls
    with pytest.raises(ExternalServiceError):
        await cb.call(CallSequenceMock([{"data": "irrelevant"}]))

    # Step 3: Timeout expires -> HALF_OPEN on next call
    original_time = time.time()
    with patch("time.time", return_value=original_time + timeout + 0.01):
        success_func = CallSequenceMock([{"data": "service recovered"}])
        result = await cb.call(success_func)

    # Step 4: CLOSED state after successful recovery
    assert result == {"data": "service recovered"}
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_circuit_breaker_does_not_reset_before_timeout():
    """Circuit should remain open if timeout has not elapsed."""
    # Arrange
    timeout = 10.0  # Long timeout
    cb = CircuitBreaker(failure_threshold=1, timeout=timeout, name="timeout_test")

    # Open circuit
    with pytest.raises(ValueError):
        await cb.call(create_always_failing_mock(1, ValueError("Fail")))

    assert cb.state == CircuitState.OPEN

    # Act: attempt call before timeout (advance time by only 1 second)
    original_time = time.time()
    with patch("time.time", return_value=original_time + 1.0):
        with pytest.raises(ExternalServiceError) as exc_info:
            await cb.call(CallSequenceMock([{"data": "irrelevant"}]))

    # Assert: circuit still open
    assert "is OPEN" in str(exc_info.value)
    assert cb.state == CircuitState.OPEN
