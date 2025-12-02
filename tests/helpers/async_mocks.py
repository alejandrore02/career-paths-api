"""Helper utilities for async testing with mocks."""

from typing import Any, Callable
from unittest.mock import AsyncMock


class CallSequenceMock:
    """
    Mock that returns different values/raises different exceptions on each call.
    
    Useful for testing retry logic and circuit breaker behavior.
    
    Example:
        # Fail twice, then succeed
        mock = CallSequenceMock([
            Exception("First failure"),
            Exception("Second failure"),
            {"result": "success"}
        ])
        
        async with pytest.raises(Exception):
            await mock()  # First call raises
        async with pytest.raises(Exception):
            await mock()  # Second call raises
        result = await mock()  # Third call returns success
    """

    def __init__(self, sequence: list[Any]):
        """
        Initialize with sequence of return values or exceptions.
        
        Args:
            sequence: List of values to return or exceptions to raise.
                     If item is an Exception, it will be raised.
                     Otherwise, it will be returned.
        """
        self.sequence = sequence
        self.call_count = 0

    async def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the mock call."""
        if self.call_count >= len(self.sequence):
            raise RuntimeError(
                f"CallSequenceMock exhausted: {self.call_count} calls "
                f"but only {len(self.sequence)} items in sequence"
            )

        item = self.sequence[self.call_count]
        self.call_count += 1

        if isinstance(item, Exception):
            raise item
        return item

    def reset(self) -> None:
        """Reset call counter."""
        self.call_count = 0


def create_failing_mock(
    fail_times: int,
    exception: Exception | None = None,
    success_value: Any = {"status": "success"},
) -> CallSequenceMock:
    """
    Create a mock that fails N times then succeeds.
    
    Args:
        fail_times: Number of times to fail before succeeding
        exception: Exception to raise (default: ValueError)
        success_value: Value to return on success
        
    Returns:
        CallSequenceMock configured to fail then succeed
        
    Example:
        mock = create_failing_mock(fail_times=2)
        # First 2 calls raise ValueError, 3rd returns success
    """
    if exception is None:
        exception = ValueError("Simulated failure")

    sequence = [exception] * fail_times + [success_value]
    return CallSequenceMock(sequence)


def create_always_failing_mock(
    attempts: int,
    exception: Exception | None = None,
) -> CallSequenceMock:
    """
    Create a mock that always fails for N attempts.
    
    Args:
        attempts: Number of attempts that will fail
        exception: Exception to raise (default: ValueError)
        
    Returns:
        CallSequenceMock configured to always fail
    """
    if exception is None:
        exception = ValueError("Persistent failure")

    sequence = [exception] * attempts
    return CallSequenceMock(sequence)
