"""Market research API routes.

This module defines endpoints that automate competitor research in the
education technology (EdTech) and learning management system (LMS)
industries. It provides functions to discover relevant companies based
on keywords, generate structured profiles from public sources, list
companies already stored in the database, and refresh an existing
profile as new information becomes available.

The routes use the same API key authentication as the chat endpoints
and rely on the ``openai_client.generate`` helper to call the language
model. By centralising the competitor research logic here, the system
exposes a clean and predictable API for the frontend without exposing
model prompts or internal details.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from html import unescape
from typing import List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.openai_client import generate
from ...core.security import get_api_key
from ...db.models import Company
from ..deps import get_db
from ...schemas.company import (
    CompanyListResponse,
    CompanyProfileRequest,
    CompanyResponse,
    DiscoverRequest,
    DiscoverResponse,
    DiscoveredCompany,
)


router = APIRouter(prefix="/market", tags=["market"], dependencies=[Depends(get_api_key)])


# ---------------------------------------------------------------------------
# Helper functions for fetching public data
# ---------------------------------------------------------------------------

async def fetch_wikipedia_extract(title: str) -> str:
    """Fetch the introductory extract from Wikipedia for a given page title.

    Args:
        title: The page title, e.g. "Moodle" or "Canvas LMS". Spaces will be
            replaced with underscores.  If the request fails or the page
            does not exist, an empty string is returned.

    Returns:
        The plain‑text extract from Wikipedia's REST API.
    """
    api_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title.replace(' ', '_')}"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(api_url, headers={"User-Agent": "ConstructorCopilotBot/1.0"})
            if resp.status_code == 200:
                data = resp.json()
                return data.get("extract", "")
    except Exception:
        pass
    return ""


async def fetch_website_text(url: str) -> str:
    """Fetch and extract visible text from a website.

    The function retrieves the HTML content of the given URL and strips out
    scripts, styles and tags to produce a plain‑text representation.  Only
    the first few thousand characters are returned to keep prompts concise.

    Args:
        url: The URL of the website to fetch.

    Returns:
        A cleaned plain‑text string with collapsed whitespace, or an empty
        string if fetching fails.
    """
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, headers={"User-Agent": "ConstructorCopilotBot/1.0"})
            if resp.status_code == 200 and "text" in resp.headers.get("content-type", ""):
                html = resp.text
                # Remove script and style content
                html = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.DOTALL | re.IGNORECASE)
                html = re.sub(r"<style[^>]*>.*?</style>", " ", html, flags=re.DOTALL | re.IGNORECASE)
                # Strip all tags
                text = re.sub(r"<[^>]+>", " ", html)
                # Decode HTML entities
                text = unescape(text)
                # Collapse whitespace
                text = re.sub(r"\s+", " ", text)
                return text.strip()[:3000]  # limit length for prompt
    except Exception:
        pass
    return ""


async def gather_context(company_name: str, website: Optional[str]) -> str:
    """Gather context from Wikipedia and the company's website.

    This helper fetches a summary from Wikipedia and text from the
    company's official website (if provided). The returned string
    concatenates the two sources, separated by blank lines, and is used
    as context for the language model.

    Args:
        company_name: Name of the company (used for Wikipedia lookup).
        website: Optional URL of the company's official website.

    Returns:
        A combined context string consisting of the Wikipedia extract and
        website text. If neither source is available, returns an empty
        string.
    """
    parts: List[str] = []
    wiki_text = await fetch_wikipedia_extract(company_name)
    if wiki_text:
        parts.append(f"Wikipedia:\n{wiki_text}")
    if website:
        web_text = await fetch_website_text(website)
        if web_text:
            parts.append(f"Website:\n{web_text}")
    return "\n\n".join(parts)


@router.post("/discover", response_model=DiscoverResponse, summary="Discover competitors for EdTech/LMS keywords")
async def discover_companies(
    request: DiscoverRequest, db: AsyncSession = Depends(get_db)
) -> DiscoverResponse:
    """Identify a list of potential competitor companies.

    The agent uses the provided keywords to compile a list of relevant
    EdTech or LMS companies. It returns a short list of company names
    along with their websites (if known) and a brief reason for why
    they match. Discovered companies are upserted into the database if
    they don't already exist (only the name and website are stored at
    this stage). The heavy lifting of profile generation happens in
    ``/market/profile``.
    """
    # Compose a prompt instructing the model to return JSON. We ask for
    # concise reasoning alongside each entry to justify inclusion.
    keywords_str = ", ".join(request.keywords)
    system_prompt = (
        "You are a market research agent specialising in education technology. "
        "Given some keywords, return a JSON object with a list of up to {max_n} "
        "companies that operate in that domain. The JSON should have a top-level "
        "key 'companies' whose value is a list of objects. Each object must "
        "contain 'name', 'website' (null if unknown) and 'reason' explaining "
        "why the company matches the keywords. Do not wrap the JSON in markdown "
        "or backticks."
    ).format(max_n=request.max_companies)
    user_prompt = (
        f"Keywords: {keywords_str}. Provide up to {request.max_companies} relevant companies."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    # Call the language model. We set a model explicitly to avoid using any
    # agent-level defaults which may not be appropriate here.
    raw_reply = await generate(messages, model="qwen/qwen2.5-7b-instruct:free")
    # Attempt to parse the JSON response. If parsing fails we fall back to
    # returning an empty list.
    companies_list: List[DiscoveredCompany] = []
    try:
        data = json.loads(raw_reply)
        for item in data.get("companies", [])[: request.max_companies]:
            # Normalise name and website fields
            name = item.get("name")
            website = item.get("website") or None
            reason = item.get("reason") or None
            if name:
                companies_list.append(
                    DiscoveredCompany(name=name, website=website, reason=reason)
                )
                # Upsert company into DB if not present
                existing = await db.execute(select(Company).where(Company.name == name))
                company_row = existing.scalars().first()
                if not company_row:
                    new_company = Company(name=name, website=website)
                    db.add(new_company)
        await db.commit()
    except Exception:
        # If parsing fails, log and return an empty result
        companies_list = []
    return DiscoverResponse(companies=companies_list)


@router.post("/profile", response_model=CompanyResponse, summary="Generate or refresh a company profile")
async def profile_company(
    request: CompanyProfileRequest, db: AsyncSession = Depends(get_db)
) -> CompanyResponse:
    """Generate a structured profile for a single company.

    Given a company name (and optionally a website), the agent gathers
    information from public sources and produces a detailed JSON profile
    containing standardized fields. If a profile already exists in the
    database and ``force_refresh`` is False, the existing profile is
    returned without re‑querying the model. Otherwise the model is
    invoked to regenerate the profile and the database is updated.
    """
    # Check for existing company record
    existing = await db.execute(select(Company).where(Company.name == request.name))
    company = existing.scalars().first()
    if company and not request.force_refresh:
        # Return current record if no refresh is requested
        return CompanyResponse(**company.__dict__)
    # Gather public context (Wikipedia and website) to ground the profile
    context = await gather_context(request.name, request.website)
    # Compose prompt to generate a JSON profile with specific fields
    fields = [
        "category",
        "description",
        "products",
        "target_segments",
        "pricing_model",
        "country",
        "size",
        "strengths",
        "risks",
    ]
    fields_str = ", ".join(fields)
    system_prompt = (
        "You are an expert market analyst specialising in EdTech. "
        "Use the provided context from public sources to create a JSON object with the following keys: "
        "name (string), website (string or null), "
        f"{fields_str} (strings), strengths, risks, sources (semicolon separated URLs). "
        "Always include all keys, even if some values are unknown. Use null for unknown website. "
        "Do not wrap the JSON in markdown."
    )
    user_prompt = (
        f"Context:\n{context}\n\n"
        f"Company name: {request.name}. Website: {request.website or 'unknown'}. "
        "Return the JSON profile."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    raw_reply = await generate(messages, model="qwen/qwen2.5-7b-instruct:free")
    try:
        profile_data = json.loads(raw_reply)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to parse profile from model response",
        )
    # Upsert into database
    if company:
        # Update existing fields
        company.website = profile_data.get("website")
        company.category = profile_data.get("category")
        company.description = profile_data.get("description")
        company.products = profile_data.get("products")
        company.target_segments = profile_data.get("target_segments")
        company.pricing_model = profile_data.get("pricing_model")
        company.country = profile_data.get("country")
        company.size = profile_data.get("size")
        company.strengths = profile_data.get("strengths")
        company.risks = profile_data.get("risks")
        company.sources = profile_data.get("sources")
        company.last_updated = datetime.utcnow()
    else:
        company = Company(
            name=profile_data.get("name", request.name),
            website=profile_data.get("website"),
            category=profile_data.get("category"),
            description=profile_data.get("description"),
            products=profile_data.get("products"),
            target_segments=profile_data.get("target_segments"),
            pricing_model=profile_data.get("pricing_model"),
            country=profile_data.get("country"),
            size=profile_data.get("size"),
            strengths=profile_data.get("strengths"),
            risks=profile_data.get("risks"),
            sources=profile_data.get("sources"),
            last_updated=datetime.utcnow(),
        )
        db.add(company)
    await db.commit()
    await db.refresh(company)
    return CompanyResponse(**company.__dict__)


@router.get("/companies", response_model=CompanyListResponse, summary="List all stored companies")
async def list_companies(
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> CompanyListResponse:
    """Retrieve a list of all companies in the database.

    Optional query parameters allow filtering by category or partial name.
    The response contains only basic details to populate tables or
    dropdowns. For full details call ``/market/profile``.
    """
    stmt = select(Company)
    if category:
        stmt = stmt.where(Company.category == category)
    if search:
        # Simple case-insensitive substring match on name
        stmt = stmt.where(Company.name.ilike(f"%{search}%"))
    result = await db.execute(stmt)
    companies = result.scalars().all()
    return CompanyListResponse(companies=[CompanyResponse(**c.__dict__) for c in companies])


@router.post("/companies/{company_id}/refresh", response_model=CompanyResponse, summary="Refresh an existing company profile")
async def refresh_company(
    company_id: int, db: AsyncSession = Depends(get_db)
) -> CompanyResponse:
    """Re-run the profile generation for a stored company.

    This endpoint triggers a fresh call to the LLM using the stored
    company name and website. The existing record is overwritten with
    the new attributes and the ``last_updated`` timestamp is updated.
    """
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalars().first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    # Use the profile endpoint logic with force_refresh=True
    req = CompanyProfileRequest(name=company.name, website=company.website, force_refresh=True)
    return await profile_company(req, db)
