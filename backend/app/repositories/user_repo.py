"""
User repository functions.

Provide database operations for the ``User`` model. By keeping database
queries in repositories, business logic in services remains clean and
testable.
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import User


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Return a user by their email address, or None if not found."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def create_user(db: AsyncSession, email: str, hashed_password: str) -> User:
    """Create and persist a new user."""
    user = User(email=email, hashed_password=hashed_password)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user