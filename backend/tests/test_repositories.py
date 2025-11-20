"""
Tests for repository functions.
"""

import pytest

from sqlalchemy.ext.asyncio import AsyncSession

import asyncio

from app.db.session import async_session, engine
from app.db.models import Base, User
from app.repositories.user_repo import create_user, get_user_by_email


@pytest.mark.asyncio
async def test_create_and_get_user():
    # Ensure tables are created
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        user = await create_user(session, "test@example.com", "secret")
        fetched = await get_user_by_email(session, "test@example.com")
        assert fetched is not None
        assert fetched.email == "test@example.com"
