"""
Background tasks for the AI agent backend.

This module defines both scheduled jobs (via APScheduler) and Celery tasks for
long-running operations. Celery tasks are used when the workload is heavy and
should be executed asynchronously in a worker process, while the scheduler is
used for periodic maintenance jobs such as cleanup or analytics aggregation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

try:
    from celery import shared_task  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    # Provide a dummy decorator when Celery isn't installed. The dummy decorator
    # simply returns the function unchanged so that tests can run without Celery.
    def shared_task(*args, **kwargs):  # type: ignore
        def wrapper(func):
            return func
        return wrapper

from .scheduler import scheduler
from ..core.celery_app import celery_app


def register_tasks() -> None:
    """Register recurring tasks with the scheduler.

    At application startup, call this function to register any periodic
    maintenance tasks. For example, you might schedule regular cleanup of
    outdated chat sessions or aggregate usage analytics.
    """
    # Example: schedule a dummy task every hour
    scheduler.add_job(dummy_task, "interval", hours=1)


async def dummy_task() -> None:
    """A simple scheduled job that logs the current time."""
    print(f"Dummy task executed at {datetime.utcnow()}")


@celery_app.task(bind=True)
def run_agent_task(self, conversation: list[dict[str, str]]) -> str:
    """Celery task that runs a long AI agent workflow.

    Args:
        conversation (list[dict[str, str]]): The chat history/messages as a list
            of dictionaries with ``role`` and ``content`` keys.

    Returns:
        str: Final response from the AI agent.

    Notes:
        This is a simplified example. In a real system, this task might
        orchestrate multiple tool calls, retrieval steps, or other
        computation-intensive operations. Progress updates can be emitted
        via ``self.update_state`` to provide intermediate statuses to the
        streaming API.
    """
    # Import inside the task to avoid circular dependencies
    from ..services.chat_service import handle_chat
    from ..schemas.common import Message
    import asyncio

    async def generate_response() -> str:
        # Convert dicts back into Pydantic models if necessary; here we assume
        # they already match the expected format.
        return await handle_chat([Message(**m) for m in conversation])  # type: ignore[name-defined]

    # Run the asynchronous chat handler in a synchronous Celery context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    response = loop.run_until_complete(generate_response())
    loop.close()
    return response
