"""
Script to check database schema and data.

Run this to verify that tables are created and data persists.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.db.session import async_session, engine
from app.db.models import Base, Company, ResearchJob, SourceDocument


async def check_database():
    """Check if database tables exist and show data."""
    
    print("=" * 60)
    print("DATABASE CHECK")
    print("=" * 60)
    
    # Create all tables if they don't exist
    print("\n1. Creating tables if needed...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✓ Tables created/verified")
    
    # Check companies
    print("\n2. Checking companies table...")
    async with async_session() as session:
        result = await session.execute(text("SELECT COUNT(*) FROM companies"))
        count = result.scalar()
        print(f"   Total companies: {count}")
        
        if count > 0:
            result = await session.execute(
                text("SELECT id, name, category, region, description FROM companies LIMIT 5")
            )
            print("\n   Sample companies:")
            for row in result:
                print(f"   - ID {row[0]}: {row[1]}")
                print(f"     Category: {row[2] or 'N/A'}, Region: {row[3] or 'N/A'}")
                desc = row[4] or "No description"
                print(f"     Description: {desc[:80]}...")
    
    # Check research jobs
    print("\n3. Checking research_jobs table...")
    async with async_session() as session:
        result = await session.execute(text("SELECT COUNT(*) FROM research_jobs"))
        count = result.scalar()
        print(f"   Total jobs: {count}")
        
        if count > 0:
            result = await session.execute(
                text("SELECT id, segment, status, created_at FROM research_jobs ORDER BY id DESC LIMIT 5")
            )
            print("\n   Recent jobs:")
            for row in result:
                print(f"   - Job {row[0]}: {row[1][:50]}")
                print(f"     Status: {row[2]}, Created: {row[3]}")
    
    # Check source documents
    print("\n4. Checking source_documents table...")
    async with async_session() as session:
        result = await session.execute(text("SELECT COUNT(*) FROM source_documents"))
        count = result.scalar()
        print(f"   Total source documents: {count}")
    
    print("\n" + "=" * 60)
    print("Check complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(check_database())