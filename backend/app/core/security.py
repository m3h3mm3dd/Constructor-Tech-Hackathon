"""
Security utilities for the AI agent backend.

Currently this module provides a simple API key authentication mechanism
via the ``X-API-Key`` header. Endpoints can depend on ``get_api_key``
to enforce authentication. In a production system you might replace or
augment this with OAuth2, JWT authentication, or integration with a
central identity provider.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from .config import settings


# Define the header that will carry the API key. If a request does not
# include the header, FastAPI will not automatically raise an error
# because ``auto_error`` is set to False. This gives us flexibility to
# implement custom logic in ``get_api_key``.
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_api_key(api_key_header: str | None = Depends(API_KEY_HEADER)) -> str:
    """Dependency to retrieve and validate the provided API key.

    Args:
        api_key_header (str | None): The value from the ``X-API-Key`` header,
            or ``None`` if not provided.

    Returns:
        str: The validated API key.

    Raises:
        HTTPException: If the API key is missing or invalid.
    """
    expected_key = settings.OPENAI_API_KEY
    if not api_key_header or api_key_header != expected_key:
        # Use 401 Unauthorized here rather than 403 Forbidden, because the
        # client is missing or providing incorrect credentials. See RFC 7235.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "APIKey"},
        )
    return api_key_header