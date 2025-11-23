"""
API routes for the competitor research agent.

This router exposes endpoints for starting research jobs, retrieving job
status, listing and retrieving companies, refreshing profiles, comparing
companies, getting aggregated statistics and exporting data. All business
logic is delegated to the corresponding service functions in
``services.research_service``.
"""

from __future__ import annotations

import csv
import io
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from ...db.models import Company, ResearchJob
from ...api.deps import get_db
from ...schemas.research import (
    CompanyCompareRequest,
    CompanyCompareResponse,
    CompanyDetail,
    CompanySummary,
    ResearchJobResponse,
    ResearchStartRequest,
    StatsOverviewResponse,
    SourceDocumentResponse,
)
from ...services.research_service import (
    compare_companies,
    get_stats_overview,
    refresh_company,
    start_research,
)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/research", tags=["research"])


@router.post("/start", response_model=ResearchJobResponse, status_code=status.HTTP_201_CREATED, deprecated=True)
async def start_research_job(
    request: ResearchStartRequest, db: AsyncSession = Depends(get_db)
) -> ResearchJobResponse:
    """Legacy start endpoint (replaced by sessions)."""
    return await start_research(request.segment, request.max_companies, db)


@router.get("/companies", response_model=List[CompanySummary])
async def list_companies(
    db: AsyncSession = Depends(get_db),
    segment: Optional[str] = Query(None, description="Filter by market segment"),
    category: Optional[str] = Query(None, description="Filter by category"),
    region: Optional[str] = Query(None, description="Filter by region"),
    has_ai_features: Optional[bool] = Query(None, description="Filter by AI features presence"),
    search: Optional[str] = Query(None, description="Search by company name"),
) -> List[CompanySummary]:
    """
    List all companies with optional filters.
    """
    stmt = select(Company)
    
    # Apply filters
    if segment:
        stmt = stmt.where(Company.segment == segment)
    if category:
        stmt = stmt.where(Company.category == category)
    if region:
        stmt = stmt.where(Company.region == region)
    if has_ai_features is not None:
        stmt = stmt.where(Company.has_ai_features == has_ai_features)
    if search:
        stmt = stmt.where(Company.name.ilike(f"%{search}%"))
    
    result = await db.execute(stmt)
    companies = result.scalars().all()
    return [
        CompanySummary(
            id=c.id,
            name=c.name,
            category=c.category,
            region=c.region,
            segment=c.segment,
            size_bucket=c.size_bucket,
            description=c.description,
            last_updated=c.last_updated,
            has_ai_features=c.has_ai_features,
        )
        for c in companies
    ]


@router.get("/companies/{company_id}")
async def get_company_detail(company_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    """Return a full profile for a single company including its source documents."""
    result = await db.execute(select(Company).where(Company.id == company_id))
    c = result.scalars().first()
    if not c:
        raise HTTPException(status_code=404, detail="Company not found")
    detail = CompanyDetail(
        id=c.id,
        name=c.name,
        website=c.website,
        segment=c.segment,
        category=c.category,
        region=c.region,
        size_bucket=c.size_bucket,
        description=c.description,
        background=c.background,
        products=c.products,
        target_segments=c.target_segments,
        pricing_model=c.pricing_model,
        market_position=c.market_position,
        strengths=c.strengths,
        risks=c.risks,
        has_ai_features=c.has_ai_features,
        compliance_tags=c.compliance_tags,
        last_updated=c.last_updated,
        first_discovered=c.first_discovered,
    )
    # Fetch sources
    docs = [
        SourceDocumentResponse(
            id=d.id,
            url=d.url,
            title=d.title,
            snippet=d.snippet,
            source_type=d.source_type,
            relevance_score=d.relevance_score,
            published_at=d.published_at,
        )
        for d in c.documents
    ]
    return {"company": detail, "sources": docs}


@router.post("/companies/{company_id}/refresh", response_model=CompanyDetail)
async def refresh_company_profile(company_id: int, db: AsyncSession = Depends(get_db)) -> CompanyDetail:
    """Re-run the profiling pipeline for a single company."""
    try:
        await refresh_company(company_id, db)
    except ValueError:
        raise HTTPException(status_code=404, detail="Company not found")
    # Return updated company
    result = await db.execute(select(Company).where(Company.id == company_id))
    c = result.scalars().first()
    return CompanyDetail(
        id=c.id,
        name=c.name,
        website=c.website,
        segment=c.segment,
        category=c.category,
        region=c.region,
        size_bucket=c.size_bucket,
        description=c.description,
        background=c.background,
        products=c.products,
        target_segments=c.target_segments,
        pricing_model=c.pricing_model,
        market_position=c.market_position,
        strengths=c.strengths,
        risks=c.risks,
        has_ai_features=c.has_ai_features,
        compliance_tags=c.compliance_tags,
        last_updated=c.last_updated,
        first_discovered=c.first_discovered,
    )


@router.post("/companies/compare", response_model=CompanyCompareResponse)
async def compare_companies_endpoint(
    request: CompanyCompareRequest, db: AsyncSession = Depends(get_db)
) -> CompanyCompareResponse:
    """Compare multiple companies and return structured insights."""
    return await compare_companies(request.company_ids, db)


@router.get("/stats/overview", response_model=StatsOverviewResponse)
async def stats_overview(db: AsyncSession = Depends(get_db)) -> StatsOverviewResponse:
    """Return aggregated statistics for charting and dashboards."""
    return await get_stats_overview(db)


@router.get("/export")
async def export_companies(
    db: AsyncSession = Depends(get_db),
    segment: Optional[str] = Query(None, description="Filter export by segment"),
) -> Response:
    """Export all companies (optionally filtered by segment) as a CSV file."""
    stmt = select(Company)
    if segment:
        stmt = stmt.where(Company.segment == segment)
    result = await db.execute(stmt)
    companies = result.scalars().all()
    # Prepare CSV content
    output = io.StringIO()
    writer = csv.writer(output)
    header = [
        "id",
        "name",
        "website",
        "segment",
        "category",
        "region",
        "size_bucket",
        "description",
        "background",
        "products",
        "target_segments",
        "pricing_model",
        "market_position",
        "strengths",
        "risks",
        "has_ai_features",
        "compliance_tags",
        "first_discovered",
        "last_updated",
    ]
    writer.writerow(header)
    for c in companies:
        writer.writerow([
            c.id,
            c.name,
            c.website or "",
            c.segment or "",
            c.category or "",
            c.region or "",
            c.size_bucket or "",
            c.description or "",
            c.background or "",
            c.products or "",
            c.target_segments or "",
            c.pricing_model or "",
            c.market_position or "",
            c.strengths or "",
            c.risks or "",
            str(c.has_ai_features),
            c.compliance_tags or "",
            c.first_discovered.isoformat() if c.first_discovered else "",
            c.last_updated.isoformat() if c.last_updated else "",
        ])
    csv_bytes = output.getvalue().encode("utf-8")
    headers = {
        "Content-Type": "text/csv; charset=utf-8",
        "Content-Disposition": "attachment; filename=companies.csv",
    }
    return Response(content=csv_bytes, headers=headers)


# IMPORTANT: This route MUST come last to avoid conflicts with paths like /companies, /stats, etc.
@router.get("/{job_id}", response_model=ResearchJobResponse)
async def get_research_job(job_id: int, db: AsyncSession = Depends(get_db)) -> ResearchJobResponse:
    """Retrieve the status of a research job and the companies it discovered."""
    result = await db.execute(select(ResearchJob).where(ResearchJob.id == job_id))
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    # Gather companies related to this segment
    stmt = select(Company).where(Company.segment == job.segment)
    result = await db.execute(stmt)
    companies = result.scalars().all()
    company_statuses = []
    for c in companies:
        status_str = "profiled" if c.last_updated else "pending"
        has_profile = bool(c.description)
        company_statuses.append(
            {
                "id": c.id,
                "name": c.name,
                "status": status_str,
                "last_updated": c.last_updated,
                "has_profile": has_profile,
            }
        )
    return ResearchJobResponse(
        job_id=job.id,
        segment=job.segment,
        status=job.status,
        error_message=job.error_message,
        created_at=job.created_at,
        finished_at=job.finished_at,
        companies=company_statuses,
    )
