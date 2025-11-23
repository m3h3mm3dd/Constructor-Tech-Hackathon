from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class SessionLog(BaseModel):
  id: int
  ts: datetime
  level: str
  message: str
  meta: Optional[dict] = None

  class Config:
    orm_mode = True


class CompanyCard(BaseModel):
  id: str
  name: str
  domain: Optional[str] = None
  score: Optional[int] = None
  status: str
  data_reliability: Optional[str] = None
  last_verified_at: Optional[datetime] = None
  founded_year: Optional[int] = None
  employees: Optional[int] = None
  hq_city: Optional[str] = None
  hq_country: Optional[str] = None
  primary_tags: Optional[List[str]] = None
  summary: Optional[str] = None

  class Config:
    orm_mode = True


class ChartsPayload(BaseModel):
  segmentation: Optional[list] = None
  company_scale: Optional[list] = None
  performance_matrix: Optional[list] = None
  market_evolution: Optional[list] = None


class SessionResponse(BaseModel):
  id: str
  label: str
  segment: Optional[str] = None
  status: str
  max_companies: Optional[int] = None
  companies_found: int
  charts: Optional[ChartsPayload] = None
  scoring_config: Optional[dict] = None
  created_at: datetime
  updated_at: datetime
  companies: List[CompanyCard] = []


class SessionListItem(BaseModel):
  id: str
  label: str
  status: str
  updated_at: datetime


class StartSessionRequest(BaseModel):
  segment: str = Field(..., description="User-provided label / query")
  max_companies: int = Field(3, ge=1, le=15)
  region: Optional[str] = None


class ScoringCriterion(BaseModel):
  key: str
  label: str
  weight: float


class ScoringConfig(BaseModel):
  criteria: List[ScoringCriterion]


class TrendBar(BaseModel):
  label: str
  impact: int


class TrendResponse(BaseModel):
  overview: str
  bars: List[TrendBar]


class CompanySourceItem(BaseModel):
  url: str
  label: Optional[str] = None
  source_type: Optional[str] = None

  class Config:
    orm_mode = True


class CompanyProfileResponse(BaseModel):
  id: str
  name: str
  domain: Optional[str] = None
  score: Optional[int] = None
  status: str
  data_reliability: Optional[str] = None
  last_verified_at: Optional[datetime] = None
  founded_year: Optional[int] = None
  employees: Optional[int] = None
  hq_city: Optional[str] = None
  hq_country: Optional[str] = None
  primary_tags: Optional[List[str]] = None
  summary: Optional[str] = None
  score_analysis: Optional[str] = None
  market_position: Optional[str] = None
  background: Optional[str] = None
  recent_developments: Optional[str] = None
  products_services: Optional[str] = None
  scale_reach: Optional[str] = None
  strategic_notes: Optional[str] = None
  sources: List[CompanySourceItem] = []
