"""Retry logic with exponential backoff."""

import asyncio
from functools import wraps
from typing import Any, Awaitable, Callable, TypeVar

from app.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


async def retry_with_backoff(
    func: Callable[..., Awaitable[T]],
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    *args: Any,
    **kwargs: Any,
) -> T:
    """
    Retry function with exponential backoff.
    
    Args:
        func: Async function to retry
        max_retries: Maximum number of retries (not counting the first attempt)
        initial_delay: Initial delay in seconds
        backoff_factor: Multiplier for each retry
        *args: Function arguments
        **kwargs: Function keyword arguments
        
    Returns:
        Function result
        
    Raises:
        Last exception if all retries fail
    """
    delay = initial_delay
    last_exception: Exception | None = None
    max_attempts = max_retries + 1

    for attempt in range(1, max_attempts + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt < max_attempts:
                logger.warning(
                    "Attempt %s/%s failed: %s. Retrying in %ss...",
                    attempt,
                    max_attempts,
                    e,
                    delay,
                )
                await asyncio.sleep(delay)
                delay *= backoff_factor
            else:
                logger.error("All %s attempts failed", max_attempts)

    if last_exception:
        raise last_exception

    # Muy defensivo: en teoría nunca deberías llegar aquí
    raise RuntimeError("Retry failed without exception")


def with_retry(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
):
    """
    Decorator for retrying async functions.
    
    Args:
        max_retries: Maximum number of retries
        initial_delay: Initial delay in seconds
        backoff_factor: Multiplier for each retry
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            return await retry_with_backoff(
                func,
                max_retries=max_retries,
                initial_delay=initial_delay,
                backoff_factor=backoff_factor,
                *args,
                **kwargs,
            )

        return wrapper

    return decorator