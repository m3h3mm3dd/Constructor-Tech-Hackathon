"""
Session service for managing research sessions.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import attributes, selectinload

from ..db.models import (
    CompanyProfile,
    CompanySource,
    ResearchSession,
    ResearchSessionLog,
    SessionCompany,
    TrendAnalysis,
)
from ..schemas.session import (
    ChartsPayload,
    CompanyCard,
    CompanyProfileResponse,
    CompanySourceItem,
    ScoringConfig,
    SessionListItem,
    SessionLog,
    SessionResponse,
    StartSessionRequest,
    TrendResponse,
)

logger = logging.getLogger(__name__)


def _parse_json(value: Any) -> Any:
    """Safely parse JSON fields that may be stored as strings."""
    if value is None or isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def _company_to_card(company: SessionCompany) -> CompanyCard:
    """Convert a SessionCompany ORM object into the API schema."""
    tags = _parse_json(company.primary_tags) or []
    summary = company.summary
    if not summary and company.profile:
        summary = company.profile.summary
    return CompanyCard(
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
        primary_tags=tags if isinstance(tags, list) else [],
        summary=summary,
    )


def _session_to_response(session: ResearchSession) -> SessionResponse:
    charts_data = _parse_json(session.charts) or {}
    scoring_data = _parse_json(session.scoring_config) or {}
    companies_raw: list[SessionCompany] = []
    if attributes.is_attribute_loaded(session, "companies"):
        companies_raw = session.companies or []
    companies = [_company_to_card(comp) for comp in companies_raw]

    return SessionResponse(
        id=session.id,
        label=session.label,
        segment=session.segment,
        status=session.status,
        max_companies=session.max_companies,
        companies_found=session.companies_found or 0,
        charts=ChartsPayload(**charts_data) if isinstance(charts_data, dict) else None,
        scoring_config=scoring_data if isinstance(scoring_data, dict) else {},
        created_at=session.created_at,
        updated_at=session.updated_at or session.created_at,
        companies=companies,
    )


async def start_session(segment: str, max_companies: int, db: AsyncSession) -> SessionResponse:
    """Create a new session and return the API representation."""
    session = ResearchSession(
        id=str(uuid4()),
        label=segment,
        segment=segment,
        status="PENDING",
        max_companies=max_companies or 5,
        companies_found=0,
        charts={},
        scoring_config={},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return _session_to_response(session)


async def create_session(session_data: StartSessionRequest, db: AsyncSession) -> SessionResponse:
    """Backward-compatible wrapper used by earlier code paths."""
    return await start_session(session_data.segment, session_data.max_companies, db)


async def list_sessions(db: AsyncSession, limit: int = 10, offset: int = 0) -> List[SessionListItem]:
    """List existing sessions ordered by most recent updates."""
    result = await db.execute(
        select(ResearchSession)
        .order_by(ResearchSession.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )
    sessions = result.scalars().all()
    return [
        SessionListItem(
            id=s.id,
            label=s.label,
            status=s.status,
            updated_at=s.updated_at or s.created_at,
        )
        for s in sessions
    ]


async def get_session(session_id: str, db: AsyncSession) -> SessionResponse:
    """Retrieve a session with its companies and profiles."""
    result = await db.execute(
        select(ResearchSession)
        .options(
            selectinload(ResearchSession.companies)
            .selectinload(SessionCompany.profile),
            selectinload(ResearchSession.companies)
            .selectinload(SessionCompany.sources),
        )
        .where(ResearchSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise ValueError("Session not found")
    return _session_to_response(session)


async def get_logs(session_id: str, db: AsyncSession, since: Optional[datetime] = None) -> List[SessionLog]:
    """Return ordered logs for a session."""
    session_exists = await db.get(ResearchSession, session_id)
    if not session_exists:
        raise ValueError("Session not found")

    query = select(ResearchSessionLog).where(ResearchSessionLog.session_id == session_id)
    if since:
        query = query.where(ResearchSessionLog.ts > since)
    query = query.order_by(ResearchSessionLog.ts.asc())

    result = await db.execute(query)
    logs = result.scalars().all()
    return [
        SessionLog(
            id=log.id,
            ts=log.ts,
            level=log.level,
            message=log.message,
            meta=log.meta or {},
        )
        for log in logs
    ]


async def update_scoring(session_id: str, payload: ScoringConfig, db: AsyncSession) -> Dict[str, Any]:
    """Persist scoring config for a session."""
    result = await db.execute(select(ResearchSession).where(ResearchSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise ValueError("Session not found")

    session.scoring_config = payload.model_dump()
    session.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(session)
    return session.scoring_config or {}


async def get_trends(session_id: str, db: AsyncSession) -> TrendResponse:
    """Fetch the latest trend analysis for a session."""
    result = await db.execute(
        select(TrendAnalysis)
        .where(TrendAnalysis.session_id == session_id)
        .order_by(TrendAnalysis.created_at.desc())
    )
    trend = result.scalars().first()
    if not trend:
        raise ValueError("Trend analysis not found")

    bars = _parse_json(trend.bars) or []
    return TrendResponse(
        overview=trend.overview or "",
        bars=bars if isinstance(bars, list) else [],
    )


async def get_company_profile(company_id: str, db: AsyncSession) -> CompanyProfileResponse:
    """Return a company profile including sources."""
    result = await db.execute(
        select(SessionCompany)
        .options(
            selectinload(SessionCompany.profile),
            selectinload(SessionCompany.sources),
        )
        .where(SessionCompany.id == company_id)
    )
    company = result.scalar_one_or_none()
    if not company:
        raise ValueError("Company not found")

    profile: CompanyProfile | None = company.profile
    sources = company.sources or []

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
        primary_tags=_parse_json(company.primary_tags) or [],
        summary=company.summary or (profile.summary if profile else None),
        score_analysis=profile.score_analysis if profile else None,
        market_position=profile.market_position if profile else None,
        background=profile.background if profile else None,
        recent_developments=profile.recent_developments if profile else None,
        products_services=profile.products_services if profile else None,
        scale_reach=profile.scale_reach if profile else None,
        strategic_notes=profile.strategic_notes if profile else None,
        sources=[
            CompanySourceItem(
                url=src.url,
                label=getattr(src, "label", None),
                source_type=getattr(src, "source_type", None),
            )
            for src in sources
        ],
    )


async def update_session_status(session_id: str, status: str, db: AsyncSession) -> bool:
    """Update a session's status flag."""
    result = await db.execute(select(ResearchSession).where(ResearchSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        return False
    session.status = status
    session.updated_at = datetime.utcnow()
    await db.commit()
    return True
