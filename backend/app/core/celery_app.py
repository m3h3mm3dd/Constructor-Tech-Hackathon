"""
Celery configuration for background task processing.

This module creates a Celery application configured via environment variables
defined in ``config.py``. Celery is used to offload long-running tasks (such as
complex AI computations or retrieval jobs) to a worker process, preventing
blocking of the FastAPI event loop. Redis is used as both the broker and
result backend by default, but these values can be overridden via the
``CELERY_BROKER_URL`` and ``CELERY_RESULT_BACKEND`` settings.

Usage:

    from .celery_app import celery_app
    from celery import shared_task

    @shared_task
    def long_running_job(args):
        ...

The Celery worker can be started with ``celery -A backend.app.core.celery_app worker``.
"""

from __future__ import annotations

try:
    from celery import Celery  # type: ignore[import-not-found]
except Exception as _e:  # pragma: no cover
    # Fallback Celery stub when Celery is not installed. This allows the app
    # to import the module without crashing during tests. Creating a dummy
    # Celery class that supports the minimal interface used in this module.
    class Celery:  # type: ignore
        def __init__(self, *args, **kwargs) -> None:
            raise ImportError(
                "Celery is not installed. Please install celery[redis] to enable background tasks."
            )

from .config import settings


def _get_celery_config() -> dict[str, str]:
    """Assemble Celery configuration from application settings.

    Returns:
        dict[str, str]: A dictionary of Celery configuration values.
    """
    broker_url = settings.CELERY_BROKER_URL or settings.REDIS_URL
    result_backend = settings.CELERY_RESULT_BACKEND or settings.REDIS_URL
    return {
        "broker_url": broker_url,
        "result_backend": result_backend,
        # Track start times so progress updates can show a STARTED state
        "task_track_started": True,
        # Prevent workers from prefetching multiple tasks at once. Important for long-running tasks.
        "worker_prefetch_multiplier": 1,
        # Expire results after an hour to avoid filling Redis indefinitely
        "result_expires": 3600,
    }


# Instantiate the Celery application. The name here should match the Python module path.
celery_app = Celery("backend.app")

# Load configuration from the assembled dictionary. Celery expects configuration via a dict
celery_app.conf.update(_get_celery_config())


__all__ = ["celery_app"]