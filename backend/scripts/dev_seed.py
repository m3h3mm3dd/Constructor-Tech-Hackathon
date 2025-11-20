"""
Development database seeding script.

Running this script will initialize the database schema and insert a demo
user. Use this to quickly set up a development environment. It is not
intended for production use.
"""

import asyncio
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Base, User
from app.db.session import engine, async_session


async def seed() -> None:
    # Create database tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Insert a demo user
    async with async_session() as session:
        await create_demo_user(session, email="demo@example.com", password="changeme")


async def create_demo_user(session: AsyncSession, email: str, password: str) -> None:
    """Insert a demo user into the database if it does not already exist."""
    existing = await session.execute(
        User.__table__.select().where(User.email == email)
    )
    if existing.scalar_one_or_none() is None:
        user = User(email=email, hashed_password=password)
        session.add(user)
        await session.commit()
        print(f"Created demo user {email}")
    else:
        print(f"Demo user {email} already exists")


if __name__ == "__main__":
    asyncio.run(seed())