"""
Observability utilities.

This module contains simple decorators and helpers to instrument function
execution. These can be expanded with more sophisticated metrics and
tracing if you integrate with a monitoring stack like Prometheus, Open
Telemetry, or Sentry. For now, a timing decorator is provided to log
execution durations.
"""

import logging
import time
from functools import wraps
from typing import Any, Awaitable, Callable, Coroutine, TypeVar, Union


logger = logging.getLogger(__name__)

R = TypeVar("R")


def timed(func: Callable[..., Awaitable[R]]) -> Callable[..., Coroutine[Any, Any, R]]:
    """Decorator that logs the execution time of async functions.

    Args:
        func (Callable[..., Awaitable[R]]): The async function to wrap.

    Returns:
        Callable[..., Coroutine[Any, Any, R]]: Wrapped async function that logs
            its runtime using the module logger.
    """

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> R:
        start = time.perf_counter()
        result: R = await func(*args, **kwargs)
        duration = time.perf_counter() - start
        logger.info("%s took %.4f seconds", func.__name__, duration)
        return result

    return wrapper