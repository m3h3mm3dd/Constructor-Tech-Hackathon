"""
Initialize database with proper schema.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.db.session import async_session, engine
from app.db.models import Base


async def init_database():
    """Create all tables."""
    
    print("Dropping existing tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    print("Creating fresh tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Database initialized successfully!")
    
    # Verify tables
    async with async_session() as session:
        result = await session.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ))
        tables = [row[0] for row in result.fetchall()]
        print(f"\nCreated tables: {', '.join(tables)}")


if __name__ == "__main__":
    asyncio.run(init_database())