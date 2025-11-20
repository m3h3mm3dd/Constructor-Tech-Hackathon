"""
Timing utilities for measuring execution durations.
"""

import time
from functools import wraps
from typing import Any, Callable, TypeVar

R = TypeVar("R")

def timeit(func: Callable[..., R]) -> Callable[..., R]:
    """Decorator to measure and print the execution time of a function."""
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> R:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        duration = time.perf_counter() - start
        print(f"{func.__name__} executed in {duration:.4f}s")
        return result
    return wrapper
