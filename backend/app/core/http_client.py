"""
Asynchronous HTTP client utilities.

This module provides simple wrappers around ``httpx.AsyncClient`` for
performing outgoing HTTP requests. Centralizing HTTP logic here makes
testing and error handling consistent across the codebase. Additional
functionality such as retry strategies, timeouts, or custom headers can be
added as needed.
"""

from typing import Any, Dict, Optional

import httpx


async def fetch_json(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: float | None = None,
) -> Any:
    """Perform an HTTP GET request and return the parsed JSON response.

    Args:
        url (str): The target URL to request.
        params (Optional[Dict[str, Any]]): Query string parameters.
        headers (Optional[Dict[str, str]]): Additional HTTP headers.
        timeout (float | None): Optional timeout in seconds.

    Returns:
        Any: The parsed JSON content of the response.

    Raises:
        httpx.HTTPError: If the request fails or the response cannot be parsed.
    """
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()