"""Pydantic schemas for EdTech competitor research.

This module defines request and response models for the competitor research
APIs. Schemas are used to validate incoming payloads and document API
responses in the OpenAPI schema. Fields are intentionally permissive
strings because the underlying data originates from unstructured sources
and is normalised by the LLM.

There are three families of schemas:

* **Discover** – specify keywords to discover competitors and return a
  list of company names with high‑level notes. Each discovered entry may
  include a reason explaining why the company matches the keywords.

* **Profile** – request generation of a detailed profile for a given
  company (name and optional website). The response contains a
  normalised Company model including all attributes. This schema is
  reused when returning existing companies from the database.

* **Listing** – list companies already stored in the database. Useful for
  populating a table or dropdown in the UI.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class DiscoverRequest(BaseModel):
    """Request payload for discovering EdTech/LMS competitors.

    Provide one or more keywords to steer the discovery. The agent will
    search for companies that match these keywords and return a list of
    candidates. You can limit the maximum number of results to avoid
    overly long lists. Keywords should be broad concepts or market
    segments (e.g. "learning management", "student analytics", "AI
    tutoring").
    """

    keywords: List[str] = Field(..., description="List of keywords describing the market segment.")
    max_companies: int = Field(10, description="Maximum number of companies to return.")


class DiscoveredCompany(BaseModel):
    """Single entry returned by the discovery endpoint."""

    name: str = Field(..., description="Company or product name.")
    website: Optional[str] = Field(None, description="Primary website URL if known.")
    reason: Optional[str] = Field(None, description="Explanation of why this company matches the keywords.")


class DiscoverResponse(BaseModel):
    """Response payload for discovery requests."""

    companies: List[DiscoveredCompany]


class CompanyBase(BaseModel):
    """Base fields shared across company profile schemas."""

    name: str
    website: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    products: Optional[str] = None
    target_segments: Optional[str] = None
    pricing_model: Optional[str] = None
    country: Optional[str] = None
    size: Optional[str] = None
    strengths: Optional[str] = None
    risks: Optional[str] = None
    sources: Optional[str] = None
    last_updated: datetime


class CompanyProfileRequest(BaseModel):
    """Request payload for generating or refreshing a company profile."""

    name: str = Field(..., description="Company or product name.")
    website: Optional[str] = Field(None, description="Website URL to use as context.")
    force_refresh: bool = Field(False, description="Force regeneration even if a profile exists.")


class CompanyResponse(CompanyBase):
    """Detailed company profile returned by the API."""

    id: int


class CompanyListResponse(BaseModel):
    """Response payload when listing multiple companies."""

    companies: List[CompanyResponse]
