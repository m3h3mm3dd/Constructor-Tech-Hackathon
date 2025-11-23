"""
Pydantic schemas for the competitor research API.

These models define the shape of request and response payloads for the
research endpoints. Keeping schemas in a separate module decouples
validation and documentation from business logic and database models.

The schemas are intentionally explicit about which fields are returned
to the client. When exposing company details, ``CompanyDetail``
includes all normalised attributes. ``CompanySummary`` is a lighter
weight representation used in lists and search results.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ResearchStartRequest(BaseModel):
    """Request payload to initiate a research job for a market segment."""

    segment: str = Field(..., description="Market segment description, e.g. 'university LMS platforms in Europe'.")
    max_companies: int = Field(10, description="Maximum number of companies to discover and profile.")


class ResearchJobCompanyStatus(BaseModel):
    """Status for a single company within a research job."""

    id: int
    name: str
    status: str = Field(..., description="Status of the company's profile within the job: 'pending' or 'profiled'.")
    last_updated: Optional[datetime] = None
    has_profile: bool = False


class ResearchJobResponse(BaseModel):
    """Response returned when querying a research job."""

    job_id: int = Field(..., alias="id")
    segment: str
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    finished_at: Optional[datetime] = None
    companies: List[ResearchJobCompanyStatus] = []


class CompanySummary(BaseModel):
    """Compact representation of a company used in lists and search results."""

    id: int
    name: str
    category: Optional[str] = None
    region: Optional[str] = None
    size_bucket: Optional[str] = None
    description: Optional[str] = None
    last_updated: Optional[datetime] = None
    has_ai_features: Optional[bool] = None


class CompanyDetail(BaseModel):
    """Full company profile returned to the client."""

    id: int
    name: str
    website: Optional[str] = None
    segment: Optional[str] = None
    category: Optional[str] = None
    region: Optional[str] = None
    size_bucket: Optional[str] = None
    description: Optional[str] = None
    background: Optional[str] = None
    products: Optional[str] = None
    target_segments: Optional[str] = None
    pricing_model: Optional[str] = None
    market_position: Optional[str] = None
    strengths: Optional[str] = None
    risks: Optional[str] = None
    has_ai_features: Optional[bool] = None
    compliance_tags: Optional[str] = None
    last_updated: Optional[datetime] = None
    first_discovered: Optional[datetime] = None


class SourceDocumentResponse(BaseModel):
    """Representation of a source document associated with a company."""

    id: int
    url: str
    title: Optional[str] = None
    snippet: Optional[str] = None
    source_type: Optional[str] = None
    relevance_score: Optional[float] = None
    published_at: Optional[datetime] = None


class CompanyCompareRequest(BaseModel):
    """Request payload to compare multiple companies and extract insights."""

    company_ids: List[int] = Field(..., description="List of company IDs to compare.")


class CompanyComparison(BaseModel):
    """Differentiation for a single company returned in a comparison."""

    company_id: int
    points: List[str] = []


class CompanyCompareResponse(BaseModel):
    """Response payload from the comparison endpoint."""

    common_strengths: List[str] = []
    key_differences: List[CompanyComparison] = []
    opportunity_gaps: List[str] = []


class StatsBucket(BaseModel):
    """Bucketed statistic value used in aggregated stats responses."""

    label: str
    count: int


class StatsOverviewResponse(BaseModel):
    """Aggregated statistics over the company dataset."""

    by_category: List[StatsBucket] = []
    by_region: List[StatsBucket] = []
    pricing_models: List[StatsBucket] = []
    ai_features: Dict[str, int] = {}
