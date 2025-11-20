"""
Asynchronous wrapper around the OpenRouter chat completions API.

This module encapsulates communication with the OpenRouter (OpenAI‑compatible)
chat completions endpoint.  It provides helper functions to generate
completions synchronously or as streams.  The wrapper runs blocking
OpenAI SDK calls in a background thread to avoid blocking the asyncio
event loop.  To use this client, ensure that ``OPENAI_API_KEY`` is set
in your environment or ``.env`` file.  The key must be a valid
OpenRouter key starting with ``sk-or-``.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, AsyncGenerator, Dict, Iterable, List, Optional

from openai import OpenAI, RateLimitError, APIError, AuthenticationError

from .config import settings

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# OpenRouter client configuration
#
# We point the OpenAI SDK at OpenRouter's API base URL.  OpenRouter hosts
# community models and provides an OpenAI‑compatible interface.  See
# https://openrouter.ai for details.  The default model used by the agents
# defined in ``app/llm/agent_registry.py`` is ``openai/gpt-oss-20b:free``.
_client = OpenAI(
    api_key=settings.OPENAI_API_KEY,
    base_url="https://openrouter.ai/api/v1",
)


async def generate(
    messages: List[Dict[str, Any]],
    model: str = "openai/gpt-oss-20b:free",
    tools: Optional[Iterable[Dict[str, Any]]] = None,
    stream: bool = False,
) -> str:
    """
    Generate a chat completion for the given conversation.

    Parameters
    ----------
    messages : list of dict
        A list of message objects in OpenAI chat format.  Each entry must
        include ``role`` ("system", "user", "assistant", etc.) and
        ``content``.  System messages define the agent persona.
    model : str, optional
        The model identifier to use.  Defaults to ``openai/gpt-oss-20b:free``.
    tools : iterable of dict, optional
        Reserved for future function calling support.  Currently ignored as
        the free model does not support tools.
    stream : bool, optional
        If True, returns the accumulated result of a streaming response.  If
        False, returns a full reply in one string.  Streaming is more
        efficient for long answers.

    Returns
    -------
    str
        The assistant's reply content or an error message.
    """
    # Build request arguments.  OpenRouter's API is compatible with
    # OpenAI's chat/completions endpoint.
    def call_api() -> Any:
        return _client.chat.completions.create(
            model=model,
            messages=messages,
            stream=stream,
        )

    try:
        response = await asyncio.to_thread(call_api)
    except AuthenticationError as e:
        logger.exception("OpenRouter auth error: %s", e)
        return (
            "Error: Invalid OpenRouter API key. "
            "Check OPENAI_API_KEY in the backend .env and ensure it starts with 'sk-or-'."
        )
    except RateLimitError as e:
        logger.exception("OpenRouter rate limit / insufficient quota: %s", e)
        return (
            "Error: The AI backend has exhausted the free quota for this key. "
            "Try again later or use a different key."
        )
    except APIError as e:
        logger.exception("OpenRouter API error: %s", e)
        return "Error: The AI provider returned an error. Please try again later."
    except Exception as e:
        logger.exception("Unexpected error while calling OpenRouter: %s", e)
        return "Error: Unexpected failure while talking to the AI backend."

    # Non‑streaming case: return the first choice content
    if not stream:
        if not hasattr(response, "choices") or not response.choices:
            return "Error: Empty response from the AI backend."
        return response.choices[0].message.content or ""

    # Streaming case: accumulate deltas
    chunks: List[str] = []
    for chunk in response:  # type: ignore[operator]
        try:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                chunks.append(delta.content)
        except Exception:
            continue
    return "".join(chunks)


async def generate_stream(
    messages: List[Dict[str, Any]],
    model: str = "openai/gpt-oss-20b:free",
    tools: Optional[Iterable[Dict[str, Any]]] = None,
) -> AsyncGenerator[str, None]:
    """
    Generate a streaming chat completion and yield chunks of text.

    This coroutine yields partial replies from the model as they are
    generated.  It is useful for implementing real‑time typing effects in
    client UIs.  On error, it yields a single message describing the
    problem and then stops.
    """
    def call_api() -> Any:
        return _client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
        )

    try:
        response = await asyncio.to_thread(call_api)
    except AuthenticationError as e:
        logger.exception("OpenRouter auth error (stream): %s", e)
        yield (
            "Error: Invalid OpenRouter API key. "
            "Check OPENAI_API_KEY in the backend .env and ensure it starts with 'sk-or-'."
        )
        return
    except RateLimitError as e:
        logger.exception("OpenRouter rate limit / insufficient quota (stream): %s", e)
        yield (
            "Error: The AI backend has exhausted the free quota for this key. "
            "Try again later or use a different key."
        )
        return
    except APIError as e:
        logger.exception("OpenRouter API error (stream): %s", e)
        yield "Error: The AI provider returned an error. Please try again later."
        return
    except Exception as e:
        logger.exception("Unexpected error while calling OpenRouter (stream): %s", e)
        yield "Error: Unexpected failure while talking to the AI backend."
        return

    for chunk in response:  # type: ignore[operator]
        try:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content
        except Exception:
            continue
