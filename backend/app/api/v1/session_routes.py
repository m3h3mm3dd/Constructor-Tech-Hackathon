from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...api.deps import get_db
from ...core.config import settings
from ...schemas.session import (
    StartSessionRequest,
    SessionResponse,
    SessionListItem,
    SessionLog,
    ScoringConfig,
    TrendResponse,
    CompanyProfileResponse,
)
from ...services.session_service import (
    start_session,
    list_sessions,
    get_session,
    get_logs,
    update_scoring,
    get_trends,
    get_company_profile,
)
from ...workers.tasks import run_scout_session, run_session_inline
import asyncio

router = APIRouter(prefix="/research", tags=["research-sessions"])


@router.post("/sessions/start", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def start_research_session(payload: StartSessionRequest, db: AsyncSession = Depends(get_db)) -> SessionResponse:
    session = await start_session(payload.segment, payload.max_companies, db)
    # fire-and-forget Celery task plus inline fallback to guarantee progress
    celery_used = False
    try:
        run_scout_session.delay(session.id)
        celery_used = True
    except Exception:
        celery_used = False
    # Always run inline as well to guarantee progress (comment out if you only want Celery)
    asyncio.create_task(run_session_inline(session.id))
    if not celery_used:
        print("Celery broker not reachable; running scout inline for session", session.id)
    return session


@router.get("/sessions", response_model=list[SessionListItem])
async def recent_sessions(limit: int = Query(6, ge=1, le=20), db: AsyncSession = Depends(get_db)) -> list[SessionListItem]:
    return await list_sessions(db, limit=limit)


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session_detail(session_id: str, db: AsyncSession = Depends(get_db)) -> SessionResponse:
    try:
        return await get_session(session_id, db)
    except ValueError:
        raise HTTPException(status_code=404, detail="Session not found")


@router.get("/sessions/{session_id}/logs", response_model=list[SessionLog])
async def get_session_logs(
    session_id: str,
    since: datetime | None = Query(None, description="Return logs newer than this timestamp"),
    db: AsyncSession = Depends(get_db),
) -> list[SessionLog]:
    try:
        return await get_logs(session_id, db, since)
    except ValueError:
        raise HTTPException(status_code=404, detail="Session not found")


@router.post("/sessions/{session_id}/refresh", response_model=SessionResponse)
async def refresh_session(session_id: str, db: AsyncSession = Depends(get_db)) -> SessionResponse:
    # Reuse start_session logic but with same id if exists
    try:
        session = await get_session(session_id, db)
    except ValueError:
        raise HTTPException(status_code=404, detail="Session not found")
    celery_used = False
    try:
        run_scout_session.delay(session.id)
        celery_used = True
    except Exception:
        celery_used = False
    asyncio.create_task(run_session_inline(session.id))
    if not celery_used:
        print("Celery broker not reachable; running scout inline for session", session.id)
    return session


@router.get("/sessions/{session_id}/scoring", response_model=dict)
async def get_scoring(session_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    try:
        session = await get_session(session_id, db)
        return session.scoring_config or {}
    except ValueError:
        raise HTTPException(status_code=404, detail="Session not found")


@router.put("/sessions/{session_id}/scoring", response_model=dict)
async def put_scoring(session_id: str, payload: ScoringConfig, db: AsyncSession = Depends(get_db)) -> dict:
    try:
        return await update_scoring(session_id, payload, db)
    except ValueError:
        raise HTTPException(status_code=404, detail="Session not found")


@router.get("/sessions/{session_id}/trends", response_model=TrendResponse)
async def get_session_trends(session_id: str, db: AsyncSession = Depends(get_db)) -> TrendResponse:
    try:
        return await get_trends(session_id, db)
    except ValueError:
        raise HTTPException(status_code=404, detail="Trend analysis not found")


@router.get("/session-companies/{company_id}", response_model=CompanyProfileResponse)
async def get_session_company(company_id: str, db: AsyncSession = Depends(get_db)) -> CompanyProfileResponse:
    try:
        return await get_company_profile(company_id, db)
    except ValueError:
        raise HTTPException(status_code=404, detail="Company not found")
