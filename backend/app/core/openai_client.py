"""
Asynchronous wrapper around an OpenAI-compatible chat API.

This module defaults to Groq's free Llama 3.1 models using the
OpenAI-compatible endpoint at https://api.groq.com/openai/v1. Two helper
functions are provided to generate completions either in a single response
or as a streamed generator. These helpers run blocking SDK calls in a
worker thread via ``asyncio.to_thread`` to avoid blocking the event loop.

If you wish to change models or providers, set ``LLM_API_KEY`` and
``LLM_API_BASE`` in ``.env`` (or fallback to ``OPENAI_API_KEY`` for
OpenRouter/OpenAI). Update ``settings.LLM_MODEL`` to point at the model
you want to call.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, AsyncGenerator, Dict, Iterable, List, Optional

from openai import OpenAI, RateLimitError, APIError, AuthenticationError, APIStatusError, OpenAIError

from .config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Client configuration (lazy)
# ---------------------------------------------------------------------------
def _get_client() -> OpenAI:
    api_key = settings.LLM_API_KEY or settings.OPENAI_API_KEY
    if not api_key:
        raise OpenAIError(
            "Missing LLM_API_KEY (or OPENAI_API_KEY). Set it in backend/.env before running the app/worker."
        )
    return OpenAI(api_key=api_key, base_url=settings.LLM_API_BASE)


async def generate(
    messages: List[Dict[str, Any]],
    model: str | None = None,
    tools: Optional[Iterable[Dict[str, Any]]] = None,
    stream: bool = False,
    max_tokens: int = 4000,  # Reduced from default to avoid credit issues
) -> str:
    """Generate a single chat completion.

    Args:
        messages: A list of message dicts following the OpenAI chat format.
        model: Model name to use. Defaults to a freely available OpenRouter model.
        tools: Currently ignored. Tools are not supported in OpenRouter free models.
        stream: When True, streaming will accumulate all chunks before return.
        max_tokens: Maximum tokens to generate. Default 4000 to avoid credit issues.

    Returns:
        The full assistant reply text, or an error string if something goes wrong.
    """
    try:
        client = _get_client()
    except OpenAIError as e:
        return str(e)

    # Use the configured model if none is explicitly provided. This allows
    # callers to override the model on a per‑request basis while keeping
    # ``settings.LLM_MODEL`` as the sensible default.
    selected_model = model or settings.LLM_MODEL
    params: Dict[str, Any] = {
        "model": selected_model,
        "messages": messages,
        "stream": stream,
        "max_tokens": max_tokens,
    }
    # Tools are not passed through for now; free OpenRouter models do not
    # support function/tool calling.  If provided, silently ignore.
    def call_api() -> Any:
        return client.chat.completions.create(**params)

    try:
        response = await asyncio.to_thread(call_api)
    except AuthenticationError as e:
        logger.exception("OpenAI auth error (invalid API key): %s", e)
        return (
            "Error: Invalid API key. "
            "Check OPENAI_API_KEY in the backend .env and make sure it's correct."
        )
    except APIStatusError as e:
        if e.status_code == 402:
            logger.exception("OpenAI insufficient credits: %s", e)
            return (
                "Error: Insufficient credits on OpenRouter. "
                "Please add credits at https://openrouter.ai/settings/credits "
                "or use a model with lower token requirements."
            )
        logger.exception("OpenAI API status error: %s", e)
        return f"Error: API returned status {e.status_code}. Please try again later."
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
    max_tokens: int = 4000,  # Reduced from default
) -> AsyncGenerator[str, None]:
    """Generate a streaming chat completion.

    This coroutine yields text chunks as they arrive from the API.  If an
    error occurs, a single descriptive string is yielded and the generator
    terminates.
    """
    try:
        client = _get_client()
    except OpenAIError as e:
        yield str(e)
        return

    selected_model = model or settings.LLM_MODEL
    params: Dict[str, Any] = {
        "model": selected_model,
        "messages": messages,
        "stream": True,
        "max_tokens": max_tokens,
    }

    def call_api() -> Any:
        return client.chat.completions.create(**params)

    try:
        response = await asyncio.to_thread(call_api)
    except AuthenticationError as e:
        logger.exception("OpenAI auth error (stream): %s", e)
        yield (
            "Error: Invalid API key. "
            "Check OPENAI_API_KEY in the backend .env and make sure it's correct."
        )
        return
    except APIStatusError as e:
        if e.status_code == 402:
            logger.exception("OpenAI insufficient credits (stream): %s", e)
            yield (
                "Error: Insufficient credits on OpenRouter. "
                "Please add credits at https://openrouter.ai/settings/credits."
            )
            return
        logger.exception("OpenAI API status error (stream): %s", e)
        yield f"Error: API returned status {e.status_code}. Please try again later."
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
