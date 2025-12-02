"""Unit tests for retry logic with exponential backoff.

Tests verify:
- Successful execution without retries
- Retry attempts with proper backoff
- Failure after max retries exhausted
- Backoff timing and exponential growth
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from app.integrations.retry import retry_with_backoff, with_retry
from tests.helpers.async_mocks import (
    CallSequenceMock,
    create_failing_mock,
    create_always_failing_mock,
)


# ============================================================================
# Tests for retry_with_backoff function
# ============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_retry_success_on_first_attempt():
    """Should succeed immediately without retries when function succeeds."""
    # Arrange
    mock_func = CallSequenceMock([{"data": "success"}])

    # Act
    result = await retry_with_backoff(
        mock_func,
        max_retries=3,
        initial_delay=0.1,
    )

    # Assert
    assert result == {"data": "success"}
    assert mock_func.call_count == 1, "Should only call once on immediate success"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_retry_succeeds_after_transient_failures():
    """Should retry and succeed when function fails then recovers."""
    # Arrange: fail twice, then succeed
    mock_func = create_failing_mock(
        fail_times=2,
        exception=ValueError("Transient error"),
        success_value={"data": "recovered"},
    )

    # Act: patch sleep to avoid slow tests
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        result = await retry_with_backoff(
            mock_func,
            max_retries=3,
            initial_delay=1.0,
            backoff_factor=2.0,
        )

    # Assert
    assert result == {"data": "recovered"}
    assert mock_func.call_count == 3, "Should call 3 times (2 failures + 1 success)"

    # Verify backoff delays
    assert mock_sleep.call_count == 2, "Should sleep twice (after each failure)"
    sleep_calls = [call.args[0] for call in mock_sleep.call_args_list]
    assert sleep_calls[0] == 1.0, "First retry delay should be 1.0s"
    assert sleep_calls[1] == 2.0, "Second retry delay should be 2.0s (1.0 * 2)"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_retry_fails_after_max_retries():
    """Should raise last exception when all retries exhausted."""
    # Arrange: always fail
    max_retries = 3
    max_attempts = max_retries + 1
    expected_exception = ValueError("Persistent failure")

    mock_func = create_always_failing_mock(
        attempts=max_attempts,
        exception=expected_exception,
    )

    # Act & Assert
    with patch("asyncio.sleep", new_callable=AsyncMock):
        with pytest.raises(ValueError) as exc_info:
            await retry_with_backoff(
                mock_func,
                max_retries=max_retries,
                initial_delay=0.01,
            )

    assert "Persistent failure" in str(exc_info.value)
    assert mock_func.call_count == max_attempts, f"Should attempt {max_attempts} times"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_retry_exponential_backoff():
    """Should apply exponential backoff with correct delays."""
    # Arrange
    mock_func = create_always_failing_mock(
        attempts=4,
        exception=RuntimeError("Always fails"),
    )

    # Act
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        with pytest.raises(RuntimeError):
            await retry_with_backoff(
                mock_func,
                max_retries=3,
                initial_delay=1.0,
                backoff_factor=3.0,
            )

    # Assert: verify exponential growth
    sleep_calls = [call.args[0] for call in mock_sleep.call_args_list]
    assert sleep_calls[0] == 1.0, "First delay: 1.0"
    assert sleep_calls[1] == 3.0, "Second delay: 1.0 * 3"
    assert sleep_calls[2] == 9.0, "Third delay: 3.0 * 3"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_retry_passes_args_and_kwargs():
    """Should correctly pass arguments to the wrapped function."""
    # Arrange
    async def mock_func(a: int, b: int, *, c: str = "default") -> dict:
        return {"sum": a + b, "c": c}

    # Act
    result = await retry_with_backoff(
        mock_func,  # func
        2,  # max_retries
        0.01,  # initial_delay
        2.0,  # backoff_factor
        10,  # a (positional arg for mock_func)
        20,  # b (positional arg for mock_func)
        c="custom",  # kwarg for mock_func
    )

    # Assert
    assert result == {"sum": 30, "c": "custom"}


# ============================================================================
# Tests for @with_retry decorator
# ============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_with_retry_decorator_success():
    """Decorator should work for successful function calls."""

    # Arrange
    @with_retry(max_retries=2, initial_delay=0.01)
    async def decorated_func() -> str:
        return "success"

    # Act
    result = await decorated_func()

    # Assert
    assert result == "success"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_with_retry_decorator_retries_on_failure():
    """Decorator should retry failed calls."""
    # Arrange: counter to track calls
    call_count = 0

    @with_retry(max_retries=3, initial_delay=0.01, backoff_factor=2.0)
    async def decorated_func() -> str:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError(f"Failure {call_count}")
        return "recovered"

    # Act
    with patch("asyncio.sleep", new_callable=AsyncMock):
        result = await decorated_func()

    # Assert
    assert result == "recovered"
    assert call_count == 3, "Should call 3 times before success"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_with_retry_decorator_raises_after_exhaustion():
    """Decorator should raise when retries exhausted."""

    # Arrange
    @with_retry(max_retries=2, initial_delay=0.01)
    async def decorated_func() -> None:
        raise ConnectionError("Always fails")

    # Act & Assert
    with patch("asyncio.sleep", new_callable=AsyncMock):
        with pytest.raises(ConnectionError) as exc_info:
            await decorated_func()

    assert "Always fails" in str(exc_info.value)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_with_retry_decorator_preserves_function_metadata():
    """Decorator should preserve original function name and docstring."""

    # Arrange
    @with_retry(max_retries=1, initial_delay=0.01)
    async def my_special_function() -> int:
        """This is a special function."""
        return 42

    # Assert
    assert my_special_function.__name__ == "my_special_function"
    assert my_special_function.__doc__ is not None and "special function" in my_special_function.__doc__


# ============================================================================
# Edge cases and integration scenarios
# ============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_retry_with_zero_retries():
    """Should only attempt once when max_retries=0."""
    # Arrange
    mock_func = create_always_failing_mock(
        attempts=1,
        exception=ValueError("Immediate failure"),
    )

    # Act & Assert
    with pytest.raises(ValueError):
        await retry_with_backoff(
            mock_func,
            max_retries=0,
            initial_delay=0.01,
        )

    assert mock_func.call_count == 1, "Should only attempt once with max_retries=0"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_retry_with_different_exception_types():
    """Should propagate different exception types correctly."""
    # Arrange
    exceptions = [
        TimeoutError("Timeout 1"),
        ConnectionError("Connection lost"),
        ValueError("Invalid data"),
    ]
    mock_func = CallSequenceMock(exceptions)

    # Act & Assert: should raise the last exception
    with patch("asyncio.sleep", new_callable=AsyncMock):
        with pytest.raises(ValueError) as exc_info:
            await retry_with_backoff(
                mock_func,
                max_retries=2,
                initial_delay=0.01,
            )

    assert "Invalid data" in str(exc_info.value)
    assert mock_func.call_count == 3
