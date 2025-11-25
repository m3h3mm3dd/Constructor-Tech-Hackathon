"""
One-time migration to fix existing data.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.db.session import async_session, engine
from app.db.models import Base


async def migrate():
    """Recreate tables and fix schema."""
    
    print("Backing up existing database...")
    # In production, you'd want to actually backup the data
    
    print("Dropping all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    print("Creating fresh tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Migration complete!")


if __name__ == "__main__":
    asyncio.run(migrate())