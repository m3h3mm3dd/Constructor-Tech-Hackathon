import logging
import random
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import (
    ResearchSession,
    ResearchSessionLog,
    SessionCompany,
    CompanyProfile,
    CompanySource,
    TrendAnalysis,
)
from ..schemas.session import (
    SessionResponse,
    SessionListItem,
    SessionLog,
    CompanyCard,
    ChartsPayload,
    ScoringConfig,
    TrendResponse,
    CompanyProfileResponse,
)

logger = logging.getLogger(__name__)


async def start_session(segment: str, max_companies: int, db: AsyncSession) -> SessionResponse:
    session = ResearchSession(
        id=str(uuid.uuid4()),
        label=segment,
        segment=segment,
        status="RUNNING",
        max_companies=max_companies,
        companies_found=0,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    await append_log(db, session.id, "info", f'SCOUT Activated. Target: "{segment}"')
    await append_log(db, session.id, "info", "Preparing discovery pipeline...")
    return await get_session(session.id, db)


async def append_log(db: AsyncSession, session_id: str, level: str, message: str, meta: Optional[dict] = None) -> None:
    log = ResearchSessionLog(session_id=session_id, level=level, message=message, meta=meta or {})
    db.add(log)
    await db.commit()


async def list_sessions(db: AsyncSession, limit: int = 6) -> List[SessionListItem]:
    stmt = (
        select(ResearchSession)
        .order_by(desc(ResearchSession.updated_at))
        .limit(limit)
    )
    result = await db.execute(stmt)
    sessions = result.scalars().all()
    return [
        SessionListItem(
            id=s.id,
            label=s.label,
            status=s.status,
            updated_at=s.updated_at or s.created_at or datetime.utcnow(),
        )
        for s in sessions
    ]


async def get_session(session_id: str, db: AsyncSession) -> SessionResponse:
    result = await db.execute(
        select(ResearchSession)
        .options(
            selectinload(ResearchSession.companies).selectinload(SessionCompany.profile),
            selectinload(ResearchSession.companies).selectinload(SessionCompany.sources),
        )
        .where(ResearchSession.id == session_id)
    )
    session = result.scalars().first()
    if not session:
        raise ValueError("Session not found")

    # Preload companies
    companies: List[SessionCompany] = session.companies  # type: ignore[attr-defined]
    company_cards = [
        CompanyCard(
            id=c.id,
            name=c.name,
            domain=c.domain,
            score=c.score,
            status=c.status,
            data_reliability=c.data_reliability,
            last_verified_at=c.last_verified_at,
            founded_year=c.founded_year,
            employees=c.employees,
            hq_city=c.hq_city,
            hq_country=c.hq_country,
            primary_tags=c.primary_tags or [],
            summary=c.summary,
        )
        for c in companies
    ]

    charts_payload = ChartsPayload(**(session.charts or {})) if session.charts else None

    return SessionResponse(
        id=session.id,
        label=session.label,
        segment=session.segment,
        status=session.status,
        max_companies=session.max_companies,
        companies_found=session.companies_found,
        charts=charts_payload,
        scoring_config=session.scoring_config or {},
        created_at=session.created_at,
        updated_at=session.updated_at,
        companies=company_cards,
    )


async def get_logs(session_id: str, db: AsyncSession, since: Optional[datetime] = None) -> List[SessionLog]:
    stmt = select(ResearchSessionLog).where(ResearchSessionLog.session_id == session_id)
    if since:
        stmt = stmt.where(ResearchSessionLog.ts > since)
    stmt = stmt.order_by(ResearchSessionLog.ts)
    result = await db.execute(stmt)
    logs = result.scalars().all()
    return [
        SessionLog(
            id=l.id,
            ts=l.ts,
            level=l.level,
            message=l.message,
            meta=l.meta,
        )
        for l in logs
    ]


async def save_trends(session_id: str, overview: str, bars: list[dict], db: AsyncSession) -> TrendResponse:
    trend = TrendAnalysis(session_id=session_id, overview=overview, bars=bars)
    db.add(trend)
    await db.commit()
    return TrendResponse(overview=overview, bars=bars)


async def get_trends(session_id: str, db: AsyncSession) -> TrendResponse:
    result = await db.execute(
        select(TrendAnalysis).where(TrendAnalysis.session_id == session_id).order_by(desc(TrendAnalysis.created_at))
    )
    trend = result.scalars().first()
    if not trend:
        raise ValueError("Trend analysis not found")
    return TrendResponse(overview=trend.overview or "", bars=trend.bars or [])


async def get_company_profile(company_id: str, db: AsyncSession) -> CompanyProfileResponse:
    result = await db.execute(
        select(SessionCompany)
        .options(
            selectinload(SessionCompany.profile),
            selectinload(SessionCompany.sources),
        )
        .where(SessionCompany.id == company_id)
    )
    company = result.scalars().first()
    if not company:
        raise ValueError("Company not found")
    profile: CompanyProfile | None = company.profile  # type: ignore[attr-defined]
    sources: list[CompanySource] = company.sources  # type: ignore[attr-defined]
    return CompanyProfileResponse(
        id=company.id,
        name=company.name,
        domain=company.domain,
        score=company.score,
        status=company.status,
        data_reliability=company.data_reliability,
        last_verified_at=company.last_verified_at,
        founded_year=company.founded_year,
        employees=company.employees,
        hq_city=company.hq_city,
        hq_country=company.hq_country,
        primary_tags=company.primary_tags or [],
        summary=profile.summary if profile else company.summary,
        score_analysis=profile.score_analysis if profile else None,
        market_position=profile.market_position if profile else None,
        background=profile.background if profile else None,
        recent_developments=profile.recent_developments if profile else None,
        products_services=profile.products_services if profile else None,
        scale_reach=profile.scale_reach if profile else None,
        strategic_notes=profile.strategic_notes if profile else None,
        sources=[
            {"url": s.url, "label": s.label, "source_type": s.source_type}
            for s in sources
        ],
    )


async def update_scoring(session_id: str, scoring: ScoringConfig, db: AsyncSession) -> dict:
    result = await db.execute(select(ResearchSession).where(ResearchSession.id == session_id))
    session = result.scalars().first()
    if not session:
        raise ValueError("Session not found")
    session.scoring_config = scoring.dict()
    await db.commit()
    return session.scoring_config


# ---------------------------------------------------------------------------
# Helpers for mock chart building (deterministic fallback when no LLM)
# ---------------------------------------------------------------------------

def build_default_charts(companies: List[SessionCompany]) -> dict:
    tag_counts = {}
    for c in companies:
        for tag in (c.primary_tags or []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    segmentation = [{"label": k, "value": v} for k, v in tag_counts.items()]

    company_scale = [{"name": c.name, "employees": c.employees or random.randint(200, 5000)} for c in companies]
    performance_matrix = [{"name": c.name, "score": c.score or random.randint(60, 95)} for c in companies]
    market_evolution = []
    base_year = 1995
    for idx, c in enumerate(companies):
        year = c.founded_year or (base_year + (idx * 3))
        year = max(1980, min(2025, year))
        market_evolution.append({
            "name": c.name,
            "year": year,
            "score": c.score or random.randint(60, 95),
            "size": max(1, (c.employees or 500) // 500),
        })
    return {
        "segmentation": segmentation,
        "company_scale": company_scale,
        "performance_matrix": performance_matrix,
        "market_evolution": market_evolution,
    }
