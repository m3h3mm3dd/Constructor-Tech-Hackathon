"""
Web search client for the competitor research agent.

This module abstracts calls to a generic search provider. It uses
``httpx`` under the hood to perform asynchronous HTTP GET requests. The
search API must be configured via environment variables ``SEARCH_API_KEY``
and ``SEARCH_API_BASE_URL`` in the ``.env`` file. If these variables are
not set, the search functions will raise descriptive errors instead of
performing any network calls.

The return type of the search function is a list of dictionaries with
``title``, ``url`` and ``snippet`` keys. These are intentionally
simple; callers can attach additional fields as required. When a
provider returns more fields, this function attempts to normalise
common names (``link`` -> ``url``, ``description`` -> ``snippet``). If
parsing fails, unknown fields are ignored.

Example usage::

    from app.core.search import search_web

    results = await search_web("Moodle LMS pricing", num_results=5)
    for item in results:
        print(item["title"], item["url"])

Implementations for specific providers can be plugged in by
customising the ``SEARCH_API_BASE_URL``. The default implementation
assumes a simple GET endpoint that accepts ``q`` and ``num`` query
parameters and returns a JSON object with an ``items`` list.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from .config import settings

logger = logging.getLogger(__name__)


class SearchError(Exception):
    """Custom exception raised when search fails due to configuration issues."""

    pass


async def search_web(query: str, num_results: int = 5) -> List[Dict[str, Any]]:
    """Perform a web search using the configured provider.

    Args:
        query: The search query string.
        num_results: Maximum number of results to return.

    Returns:
        A list of dictionaries with ``title``, ``url`` and ``snippet`` keys.

    Raises:
        SearchError: If the search configuration is incomplete or a network
            error occurs.
    """
    base_url = settings.SEARCH_API_BASE_URL
    api_key = settings.SEARCH_API_KEY
    if not base_url or not api_key:
        raise SearchError(
            "Search API configuration missing. Please set SEARCH_API_BASE_URL and SEARCH_API_KEY in your .env file."
        )
    # Construct request parameters. The names ``q`` and ``num`` are used by
    # many providers; adjust as necessary for specific vendors. The API key is
    # passed via an Authorization header to avoid leaking it in logs.
    params = {"q": query, "num": num_results}
    headers = {"Authorization": f"Bearer {api_key}", "User-Agent": "CompetitorResearchBot/1.0"}
    url = base_url.rstrip("/") + "/search"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            data: Any = resp.json()
    except Exception as exc:
        logger.exception("Failed to perform web search: %s", exc)
        raise SearchError(f"Search request failed: {exc}") from exc
    # Attempt to normalise the response. We expect a top‑level ``items`` list
    # with objects that contain at least a link and title. Different APIs
    # structure their payloads differently; the logic below tries to map
    # common field names to our schema. Unknown items are skipped.
    results: List[Dict[str, Any]] = []
    items: Optional[List[Any]] = None
    if isinstance(data, dict):
        items = data.get("items") or data.get("results") or data.get("documents")
    elif isinstance(data, list):
        items = data  # assume bare list
    if not items:
        return results
    for item in items[:num_results]:
        try:
            title = item.get("title") or item.get("name") or ""
            url = item.get("url") or item.get("link") or ""
            snippet = item.get("snippet") or item.get("description") or item.get("snippet_text") or ""
            if not url:
                continue
            results.append({"title": title, "url": url, "snippet": snippet})
        except Exception:
            continue
    return results