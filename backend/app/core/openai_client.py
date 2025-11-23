"""
Asynchronous wrapper around the OpenAI chat API.

This module encapsulates communication with the OpenAI-compatible chat
completion API.  The backend uses OpenRouter as the model provider, so
the OpenAI client is configured with ``base_url`` pointing at
``https://openrouter.ai/api/v1``.  Two helper functions are provided to
generate completions either in a single response or as a streamed
generator.  These helpers run blocking SDK calls in a worker thread
via ``asyncio.to_thread`` to avoid blocking the event loop.

If you wish to change models or providers, modify the ``_client``
configuration below and update default model names in the function
signatures.  To use this client, ensure that ``OPENAI_API_KEY`` is
defined in your ``.env`` file.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, AsyncGenerator, Dict, Iterable, List, Optional

from openai import OpenAI, RateLimitError, APIError, AuthenticationError

from .config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Client configuration
# ---------------------------------------------------------------------------
# We use OpenRouter as the underlying provider for chat completions.  The
# OpenAI SDK accepts a custom ``base_url`` which is forwarded to
# OpenRouter.  All OpenRouter models are namespaced under a provider
# prefix, e.g. ``openai/gpt-4o-mini`` or ``qwen/qwen2.5-7b-instruct:free``.
_client = OpenAI(
    api_key=settings.OPENAI_API_KEY,
    base_url="https://openrouter.ai/api/v1",  # route all calls through OpenRouter
)


async def generate(
    messages: List[Dict[str, Any]],
    model: str | None = None,
    tools: Optional[Iterable[Dict[str, Any]]] = None,
    stream: bool = False,
) -> str:
    """Generate a single chat completion.

    Args:
        messages: A list of message dicts following the OpenAI chat format.
        model: Model name to use. Defaults to a freely available OpenRouter model.
        tools: Currently ignored. Tools are not supported in OpenRouter free models.
        stream: When True, streaming will accumulate all chunks before return.

    Returns:
        The full assistant reply text, or an error string if something goes wrong.
    """
    # Use the configured model if none is explicitly provided. This allows
    # callers to override the model on a per‑request basis while keeping
    # ``settings.LLM_MODEL`` as the sensible default.
    selected_model = model or settings.LLM_MODEL
    params: Dict[str, Any] = {
        "model": selected_model,
        "messages": messages,
        "stream": stream,
    }
    # Tools are not passed through for now; free OpenRouter models do not
    # support function/tool calling.  If provided, silently ignore.
    def call_api() -> Any:
        return _client.chat.completions.create(**params)

    try:
        response = await asyncio.to_thread(call_api)
    except AuthenticationError as e:
        logger.exception("OpenAI auth error (invalid API key): %s", e)
        return (
            "Error: Invalid API key. "
            "Check OPENAI_API_KEY in the backend .env and make sure it’s correct."
        )
    except RateLimitError as e:
        logger.exception("OpenAI rate limit / insufficient quota: %s", e)
        return (
            "Error: The AI backend has reached its rate limit on this key. "
            "Please try again later or use a different key."
        )
    except APIError as e:
        logger.exception("OpenAI API error: %s", e)
        return "Error: The AI provider returned an error. Please try again later."
    except Exception as e:
        logger.exception("Unexpected error while calling OpenAI: %s", e)
        return "Error: Unexpected failure while talking to the AI backend."

    # Non-streaming response returns a ChatCompletion object
    if not stream:
        if not response.choices:
            return "Error: Empty response from AI backend."
        return response.choices[0].message.content or ""

    # Streaming mode: accumulate chunks into one string
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
    model: str | None = None,
    tools: Optional[Iterable[Dict[str, Any]]] = None,
) -> AsyncGenerator[str, None]:
    """Generate a streaming chat completion.

    This coroutine yields text chunks as they arrive from the API.  If an
    error occurs, a single descriptive string is yielded and the generator
    terminates.
    """
    selected_model = model or settings.LLM_MODEL
    params: Dict[str, Any] = {
        "model": selected_model,
        "messages": messages,
        "stream": True,
    }

    def call_api() -> Any:
        return _client.chat.completions.create(**params)

    try:
        response = await asyncio.to_thread(call_api)
    except AuthenticationError as e:
        logger.exception("OpenAI auth error (stream): %s", e)
        yield (
            "Error: Invalid API key. "
            "Check OPENAI_API_KEY in the backend .env and make sure it’s correct."
        )
        return
    except RateLimitError as e:
        logger.exception("OpenAI rate limit / insufficient quota (stream): %s", e)
        yield (
            "Error: The AI backend has reached its rate limit on this key. "
            "Please try again later or use a different key."
        )
        return
    except APIError as e:
        logger.exception("OpenAI API error (stream): %s", e)
        yield "Error: The AI provider returned an error. Please try again later."
        return
    except Exception as e:
        logger.exception("Unexpected error while calling OpenAI (stream): %s", e)
        yield "Error: Unexpected failure while talking to the AI backend."
        return

    for chunk in response:  # type: ignore[operator]
        try:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content
        except Exception:
            continue
