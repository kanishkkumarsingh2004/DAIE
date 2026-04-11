"""
Resilience and fault tolerance mechanisms for DAIE.
Includes Circuit Breaker and Retry Policy implementations.
"""

import asyncio
import logging
import time
from enum import Enum
from functools import wraps
from typing import Any, Callable, Optional, Type

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failure state - reject requests
    HALF_OPEN = "half_open"  # Testing if service is back


class CircuitBreaker:
    """
    Circuit Breaker pattern implementation to prevent cascading failures.

    States:
    - CLOSED: Requests pass through normally.
    - OPEN: Requests fail fast without calling the underlying service.
    - HALF_OPEN: A limited number of requests are allowed to test service health.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 3,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.half_open_calls = 0

    def _on_success(self):
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_calls += 1
            if self.half_open_calls >= self.half_open_max_calls:
                logger.info(f"Circuit Breaker '{self.name}' CLOSED (recovered)")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.CLOSED and self.failure_count >= self.failure_threshold:
            logger.warning(f"Circuit Breaker '{self.name}' OPEN (threshold reached)")
            self.state = CircuitState.OPEN
        elif self.state == CircuitState.HALF_OPEN:
            logger.warning(f"Circuit Breaker '{self.name}' RE-OPENED (failed in half-open)")
            self.state = CircuitState.OPEN

    def can_call(self) -> bool:
        """Check if a call is allowed based on current state."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if time.time() - (self.last_failure_time or 0) >= self.recovery_timeout:
                logger.info(f"Circuit Breaker '{self.name}' HALF-OPEN (recovery timeout passed)")
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            return self.half_open_calls < self.half_open_max_calls

        return True

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a function through the circuit breaker."""
        if not self.can_call():
            raise RuntimeError(f"Circuit Breaker '{self.name}' is OPEN. Request rejected.")

        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e


class RetryPolicy:
    """
    Retry policy with exponential backoff and jitter.
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 10.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: Optional[tuple[Type[Exception], ...]] = None,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions or (Exception,)

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a function with retries."""
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except self.retryable_exceptions as e:
                last_exception = e
                if attempt == self.max_retries:
                    break

                # Calculate delay with exponential backoff
                delay = min(self.max_delay, self.base_delay * (self.exponential_base**attempt))

                # Add jitter
                if self.jitter:
                    import random

                    delay *= 0.5 + random.random()

                logger.info(
                    f"Retry attempt {attempt + 1}/{self.max_retries} after {delay:.2f}s due to: {e}"
                )
                await asyncio.sleep(delay)

        if last_exception:
            raise last_exception

        raise RuntimeError("Retry failed without an exception (should not happen)")


def with_resilience(
    circuit_breaker: Optional[CircuitBreaker] = None, retry_policy: Optional[RetryPolicy] = None
):
    """
    Decorator to apply resilience to a function.
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):

            async def execute_actual():
                if circuit_breaker:
                    return await circuit_breaker.call(func, *args, **kwargs)
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                return func(*args, **kwargs)

            if retry_policy:
                return await retry_policy.execute(execute_actual)
            else:
                return await execute_actual()

        return wrapper

    return decorator
