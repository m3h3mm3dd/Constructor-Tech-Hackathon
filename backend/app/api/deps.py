"""
Dependency functions for FastAPI routes.

This module defines common dependencies such as obtaining a database
session or retrieving the current user. Using dependencies helps keep
route functions clean and separates cross-cutting concerns from
endpoint-specific logic. Functions here can be extended to include
authorization checks, caching, or other behaviors.
"""

from typing import AsyncGenerator

from fastapi import Depends

from ..db.session import async_session
from ..schemas.user import User


async def get_db() -> AsyncGenerator:
    """Yield an async database session for a single request cycle.

    Yields:
        AsyncSession: SQLAlchemy async session.
    """
    async with async_session() as session:
        yield session


async def get_current_user() -> User:
    """Placeholder for user retrieval.

    Returns:
        User: An anonymous user instance.

    Note:
        In a real application, this would retrieve the authenticated user
        from a token or session. For now, it returns a dummy user.
    """
    return User(id=0, email="anonymous@example.com")