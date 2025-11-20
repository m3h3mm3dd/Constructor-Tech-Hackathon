"""
Tests for the chat API endpoint.
"""

import asyncio

import pytest
from httpx import AsyncClient

from app.main import app
from app.core.config import settings


@pytest.mark.asyncio
async def test_chat_endpoint_returns_unauthorized_without_key() -> None:
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat/", json={"messages": [{"role": "user", "content": "Hello"}]}
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_chat_endpoint_with_key_returns_success() -> None:
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat/",
            json={"messages": [{"role": "user", "content": "Hello"}]},
            headers={"X-API-Key": settings.OPENAI_API_KEY},
        )
        # Since ``generate`` returns a stub response, we only check status code here.
        assert response.status_code == 200