"""Circuit breaker pattern implementation."""

import time
from enum import Enum
from typing import Any, Awaitable, Callable, TypeVar
from functools import wraps

from app.core.logging import get_logger
from app.core.errors import ExternalServiceError

logger = get_logger(__name__)

T = TypeVar("T")


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "CLOSED"  # Normal operation
    OPEN = "OPEN"  # Failing, reject requests
    HALF_OPEN = "HALF_OPEN"  # Testing if service recovered


class CircuitBreaker:
    """Circuit breaker for external service calls."""

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        name: str = "circuit_breaker",
    ) -> None:
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds to wait before attempting recovery
            name: Circuit breaker name for logging
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.name = name
        self.failure_count = 0
        self.last_failure_time: float | None = None
        self.state = CircuitState.CLOSED

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return False
        return time.time() - self.last_failure_time >= self.timeout

    async def call(self, func: Callable[..., Awaitable[T]], *args: Any, **kwargs: Any) -> T:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            ExternalServiceError: If circuit is open
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                logger.info(f"Circuit {self.name}: Attempting reset (HALF_OPEN)")
                self.state = CircuitState.HALF_OPEN
            else:
                logger.warning(f"Circuit {self.name}: OPEN, rejecting call")
                raise ExternalServiceError(
                    f"Circuit breaker '{self.name}' is OPEN",
                    details={"state": self.state, "failures": self.failure_count},
                )

        try:
            result = await func(*args, **kwargs)
            
            if self.state == CircuitState.HALF_OPEN:
                logger.info(f"Circuit {self.name}: Reset successful, closing circuit")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.last_failure_time = None
            
            return result
            
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            logger.error(
                f"Circuit {self.name}: Failure {self.failure_count}/"
                f"{self.failure_threshold} - {e}"
            )
            
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.error(f"Circuit {self.name}: OPENED due to failures")
            
            raise


def with_circuit_breaker(
    failure_threshold: int = 5,
    timeout: float = 60.0,
    name: str = "circuit_breaker",
):
    """
    Decorator for circuit breaker protection.
    
    Args:
        failure_threshold: Number of failures before opening circuit
        timeout: Seconds to wait before attempting recovery
        name: Circuit breaker name
    """
    circuit_breaker = CircuitBreaker(failure_threshold, timeout, name)
    
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            return await circuit_breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator
