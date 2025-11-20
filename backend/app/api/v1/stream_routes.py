"""
Streaming chat endpoint.

This route implements server-sent events (SSE) to stream the AI agent's
reply incrementally. While the simple implementation yields words one by
one, this pattern can be adapted for token streaming using the OpenAI API's
streaming functionality. SSE is supported natively by modern browsers and
provides a lightweight alternative to WebSockets for one-way streaming.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

try:
    # Optional: use EventSourceResponse if available. It's part of sse-starlette
    from sse_starlette.sse import EventSourceResponse  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - fallback if sse-starlette is not installed
    EventSourceResponse = None  # type: ignore

from ...core.security import get_api_key
from ...schemas.chat import ChatRequest
from ...services.chat_service import stream_chat


router = APIRouter()


@router.post("/")
async def stream_endpoint(
    request: ChatRequest,
    api_key: str = Depends(get_api_key),
) -> StreamingResponse:
    """Stream the AI agent's reply as server-sent events.

    Args:
        request (ChatRequest): Contains the conversation messages.
        api_key (str): Validated API key.

    Returns:
        StreamingResponse: A streaming response of text chunks.
    """

    async def event_stream():
        async for chunk in stream_chat(request.messages):
            # SSE format: each message starts with "data:" and ends with two newlines
            yield f"data: {chunk}\n\n"

    # Prefer EventSourceResponse if available. Otherwise fallback to StreamingResponse.
    if EventSourceResponse:
        return EventSourceResponse(event_stream())
    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/task")
async def run_task_endpoint(
    request: ChatRequest,
    api_key: str = Depends(get_api_key),
) -> StreamingResponse:
    """Run a long-running agent task in Celery and stream progress.

    This endpoint enqueues a Celery task with the conversation messages and
    streams progress updates to the client using server-sent events. The
    task emits progress via ``update_state`` calls, which are polled in a loop
    until the task completes.

    Args:
        request (ChatRequest): Chat history/messages to process.
        api_key (str): Valid API key via dependency.

    Returns:
        StreamingResponse: A stream of events including start, progress, and final
            result.
    """
    from ...workers.tasks import run_agent_task  # imported lazily to avoid circular deps
    from celery.result import AsyncResult
    import asyncio

    # Enqueue the Celery task. We pass the list of messages as plain dicts.
    messages = [m.dict(exclude_unset=True) for m in request.messages]
    async_result: AsyncResult = run_agent_task.apply_async(args=[messages])
    task_id = async_result.id

    async def sse_generator():
        # Notify client that the task was accepted
        yield f"event: start\ndata: {task_id}\n\n"
        # Poll the task for progress
        while not async_result.ready():
            # If the task has custom metadata, forward it as a progress event
            meta = async_result.info or {}
            progress = meta.get("progress")
            if progress is not None:
                yield f"event: progress\ndata: {progress}\n\n"
            await asyncio.sleep(1)
        # Once complete, send the final result
        result = async_result.result
        yield f"event: result\ndata: {result}\n\n"
    if EventSourceResponse:
        return EventSourceResponse(sse_generator())
    return StreamingResponse(sse_generator(), media_type="text/event-stream")