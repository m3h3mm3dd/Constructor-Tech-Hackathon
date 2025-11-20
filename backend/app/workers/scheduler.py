"""
Scheduler setup for background tasks.

This module configures an APScheduler instance for running background
jobs. You can register periodic tasks in ``tasks.py`` and start the
scheduler during application startup.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Create a global scheduler instance. Do not start it until the FastAPI
# application has been fully initialized to avoid race conditions.
scheduler = AsyncIOScheduler(timezone="UTC")


def start_scheduler() -> None:
    """Start the background task scheduler if not already running."""
    if not scheduler.running:
        scheduler.start()
