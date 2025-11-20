"""
Database session setup for SQLAlchemy.

Creates an async engine and sessionmaker using the database URL from
application settings. The async session factory is exported as
``async_session`` for use in dependency injection.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from ..core.config import settings


# Create an async engine. The echo flag can be set to True for verbose
# SQL logging during development.
engine = create_async_engine(settings.DB_URL, echo=False, future=True)

async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)