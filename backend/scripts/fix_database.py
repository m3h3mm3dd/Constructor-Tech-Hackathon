"""
Database diagnostic and repair script.

Run with: python scripts/fix_database.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text, select
from app.db.session import async_session, engine
from app.db.models import Base, ResearchSession, SessionCompany, CompanyProfile, CompanySource


async def fix_database():
    """Check and fix database issues."""
    
    print("=" * 70)
    print("DATABASE DIAGNOSTIC AND REPAIR")
    print("=" * 70)
    
    print("\n[1/6] Creating tables if needed...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tables created/verified")
    
    print("\n[2/6] Checking for missing timestamps...")
    async with async_session() as session:
        result = await session.execute(
            select(ResearchSession).where(
                (ResearchSession.created_at == None) | (ResearchSession.updated_at == None)
            )
        )
        sessions_to_fix = result.scalars().all()
        
        if sessions_to_fix:
            print(f"⚠️  Found {len(sessions_to_fix)} sessions with missing timestamps")
            now = datetime.utcnow()
            for s in sessions_to_fix:
                if not s.created_at:
                    s.created_at = now
                if not s.updated_at:
                    s.updated_at = now
                print(f"   Fixed: {s.id} - {s.label}")
            await session.commit()
            print(f"✅ Fixed {len(sessions_to_fix)} sessions")
        else:
            print("✅ All sessions have valid timestamps")
    
    print("\n[3/6] Checking company timestamps...")
    async with async_session() as session:
        result = await session.execute(
            select(SessionCompany).where(
                (SessionCompany.created_at == None) | (SessionCompany.updated_at == None)
            )
        )
        companies_to_fix = result.scalars().all()
        
        if companies_to_fix:
            print(f"⚠️  Found {len(companies_to_fix)} companies with missing timestamps")
            now = datetime.utcnow()
            for c in companies_to_fix:
                if not c.created_at:
                    c.created_at = now
                if not c.updated_at:
                    c.updated_at = now
                print(f"   Fixed: {c.name}")
            await session.commit()
            print(f"✅ Fixed {len(companies_to_fix)} companies")
        else:
            print("✅ All companies have valid timestamps")
    
    print("\n[4/6] Checking database integrity...")
    async with async_session() as session:
        result = await session.execute(select(ResearchSession))
        sessions = result.scalars().all()
        print(f"   Total sessions: {len(sessions)}")
        
        result = await session.execute(select(SessionCompany))
        companies = result.scalars().all()
        print(f"   Total companies: {len(companies)}")
    
    print("\n[5/6] Sample session data:")
    async with async_session() as session:
        result = await session.execute(
            select(ResearchSession)
            .order_by(ResearchSession.created_at.desc())
            .limit(3)
        )
        sessions = result.scalars().all()
        
        if sessions:
            for s in sessions:
                print(f"\n   Session: {s.label}")
                print(f"   ID: {s.id}")
                print(f"   Status: {s.status}")
                print(f"   Created: {s.created_at}")
                print(f"   Updated: {s.updated_at}")
                print(f"   Companies: {s.companies_found}")
        else:
            print("   No sessions found in database")
    
    print("\n[6/6] Testing frontend query...")
    try:
        async with async_session() as session:
            result = await session.execute(
                select(ResearchSession)
                .order_by(ResearchSession.updated_at.desc())
                .limit(6)
            )
            sessions = result.scalars().all()
            
            items = []
            for s in sessions:
                updated_at = s.updated_at or s.created_at or datetime.utcnow()
                items.append({
                    "id": s.id,
                    "label": s.label,
                    "status": s.status,
                    "updated_at": updated_at.isoformat(),
                })
            
            print(f"✅ Query successful! Would return {len(items)} sessions")
            if items:
                print(f"   Sample response: {items[0]}")
    except Exception as e:
        print(f"❌ Query failed: {e}")
        print(f"   This is the error the frontend is seeing!")
    
    print("\n" + "=" * 70)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(fix_database())