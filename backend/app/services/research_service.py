"""
Business logic for the competitor research agent.

This module implements the core pipelines described in the hackathon brief:

* Discovery – given a market segment, propose an initial set of companies to
  investigate using the language model. The discovered companies are
  upserted into the database and linked to a new ResearchJob.

* Profiling – for each company, fetch public web pages via a search API,
  extract plain text, and ask the language model to synthesise a structured
  profile. Source documents are stored in the ``source_documents`` table.

* Updating – allow refreshing a company's profile on demand.

* Statistics – compute aggregated statistics for charting purposes.

* Comparison – produce insights across multiple companies.

All functions catch and log errors but propagate meaningful exceptions to
the API layer so that HTTP responses can be generated accordingly.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.openai_client import generate
from ..core.search import SearchError, search_web
from ..core.config import settings
from ..db.models import Company, ResearchJob, SourceDocument
from ..schemas.research import (
    CompanyCompareResponse,
    CompanyComparison,
    ResearchJobCompanyStatus,
    ResearchJobResponse,
    StatsBucket,
    StatsOverviewResponse,
)

logger = logging.getLogger(__name__)


async def start_research(
    segment: str,
    max_companies: int,
    db: AsyncSession,
) -> ResearchJobResponse:
    """Kick off a competitor research job for a given market segment.

    This function performs the "sense" and initial "decide" steps: it
    invokes the language model to propose a list of companies relevant to
    ``segment``, upserts them into the database, and sequentially profiles
    each one. A ResearchJob record tracks progress and status.

    Args:
        segment: Market segment description provided by the user.
        max_companies: Maximum number of companies to discover and profile.
        db: Async database session.

    Returns:
        A ``ResearchJobResponse`` containing job metadata and company status.
    """
    # Create job in DB
    job = ResearchJob(segment=segment, status="running", created_at=datetime.utcnow())
    db.add(job)
    await db.commit()
    await db.refresh(job)
    logger.info("Started research job %s for segment '%s'", job.id, segment)

    company_statuses: List[ResearchJobCompanyStatus] = []

    try:
        # Step 1: use LLM to discover candidate companies
        discovered = await _discover_companies_via_llm(segment, max_companies)
        
        if not discovered:
            logger.warning("No companies discovered for segment: %s", segment)
            job.status = "done"
            job.error_message = "No companies found for this segment"
            job.finished_at = datetime.utcnow()
            await db.commit()
            return ResearchJobResponse(
                job_id=job.id,
                segment=job.segment,
                status=job.status,
                error_message=job.error_message,
                created_at=job.created_at,
                finished_at=job.finished_at,
                companies=[],
            )

        # Step 2: Upsert each discovered company and profile it
        for item in discovered:
            name = item.get("name")
            if not name:
                continue
                
            website = item.get("website")
            category = item.get("category")
            region = item.get("region")
            size_bucket = item.get("size_bucket")
            
            # Upsert into DB
            result = await db.execute(select(Company).where(Company.name == name))
            company: Optional[Company] = result.scalars().first()
            
            if company:
                # Update existing company
                logger.info("Updating existing company: %s", name)
                if segment and not company.segment:
                    company.segment = segment
                if category and not company.category:
                    company.category = category
                if region and not company.region:
                    company.region = region
                if size_bucket and not company.size_bucket:
                    company.size_bucket = size_bucket
                if website and not company.website:
                    company.website = website
            else:
                # Create new company
                logger.info("Creating new company: %s", name)
                company = Company(
                    name=name,
                    website=website,
                    segment=segment,
                    category=category,
                    region=region,
                    size_bucket=size_bucket,
                    first_discovered=datetime.utcnow(),
                )
                db.add(company)
            
            # Commit after each company creation/update
            await db.commit()
            await db.refresh(company)
            
            # Initialize status
            status = ResearchJobCompanyStatus(
                id=company.id,
                name=company.name,
                status="pending",
                last_updated=company.last_updated,
                has_profile=False,
            )
            
            # Profile the company
            try:
                logger.info("Profiling company: %s", company.name)
                await profile_company(company, db)
                await db.refresh(company)  # Refresh to get updated fields
                status.status = "profiled"
                status.last_updated = company.last_updated
                status.has_profile = bool(company.description)
                logger.info("Successfully profiled: %s", company.name)
            except Exception as exc:
                logger.exception("Profiling failed for %s: %s", company.name, exc)
                status.status = "failed"
                status.has_profile = False
                # Continue to next company even if this one fails
            
            company_statuses.append(status)
            
            # Commit after profiling each company
            await db.commit()

        # Mark job as done
        job.status = "done"
        job.finished_at = datetime.utcnow()
        await db.commit()
        logger.info("Completed research job %s with %d companies", job.id, len(company_statuses))

    except Exception as exc:
        logger.exception("Research job %s failed: %s", job.id, exc)
        job.status = "failed"
        job.error_message = str(exc)[:512]
        job.finished_at = datetime.utcnow()
        await db.commit()
        
        return ResearchJobResponse(
            job_id=job.id,
            segment=job.segment,
            status=job.status,
            error_message=job.error_message,
            created_at=job.created_at,
            finished_at=job.finished_at,
            companies=company_statuses,
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


async def _discover_companies_via_llm(segment: str, max_companies: int) -> List[Dict[str, str]]:
    """Ask the language model to propose a list of companies for a segment.

    The model returns a JSON string containing a list of company objects.
    Each object should include at minimum ``name``. Optionally it may
    include ``website``, ``category``, ``region`` and ``size_bucket``. If
    parsing fails, an empty list is returned.

    Args:
        segment: Market segment to explore.
        max_companies: Desired maximum number of companies.

    Returns:
        A list of dictionaries, one per proposed company.
    """
    system_prompt = (
        "You are an assistant that helps with market research in the education and LMS sector. "
        "Given a description of a market segment, propose up to {max_n} relevant companies. "
        "Return ONLY a JSON object with a top level key 'companies' whose value is a list of objects. "
        "Each company object must contain: 'name' (string), and optionally 'website', 'category', 'region', 'size_bucket'. "
        "Do not include any commentary, markdown formatting, or anything outside of the JSON."
    ).format(max_n=max_companies)
    
    user_prompt = f"Segment: {segment}. Provide up to {max_companies} companies."
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    
    try:
        raw = await generate(messages, model=settings.LLM_MODEL, max_tokens=2000)
        
        # Clean up the response - remove markdown code blocks if present
        raw = raw.strip()
        if raw.startswith("```json"):
            raw = raw[7:]
        if raw.startswith("```"):
            raw = raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()
        
        logger.info("LLM discovery response: %s", raw[:200])
        
        data = json.loads(raw)
        companies = [
            {
                "name": c.get("name"),
                "website": c.get("website"),
                "category": c.get("category"),
                "region": c.get("region"),
                "size_bucket": c.get("size_bucket"),
            }
            for c in data.get("companies", [])[:max_companies]
            if c.get("name")
        ]
        
        logger.info("Discovered %d companies", len(companies))
        return companies
        
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse discovery JSON: %s. Raw response: %s", exc, raw[:500])
        return []
    except Exception as exc:
        logger.exception("Error during company discovery: %s", exc)
        return []


async def profile_company(company: Company, db: AsyncSession) -> None:
    """Generate or refresh a structured profile for a company.

    This function performs the core "decide" step of the pipeline. It
    gathers public information via a search API and the company's own
    website, concatenates the text into a context, and asks the language
    model to produce a normalised JSON profile. All source documents are
    persisted to the ``source_documents`` table.

    Args:
        company: The Company ORM object to profile. Fields will be updated in place.
        db: Async database session.

    Returns:
        None. The company object is updated and committed to the database.
    """
    logger.info("Starting profiling for company: %s", company.name)
    
    # Build search queries
    queries = [
        f"{company.name} education platform",
        f"{company.name} LMS features",
    ]
    
    # Gather documents
    documents: List[Tuple[str, str, str]] = []  # (url, title, snippet)
    try:
        for q in queries[:2]:  # Limit to 2 queries to save time
            try:
                results = await search_web(q, num_results=2)  # Reduced from 3
                for item in results:
                    url = item.get("url")
                    title = item.get("title")
                    snippet = item.get("snippet")
                    if url and not any(d[0] == url for d in documents):
                        documents.append((url, title, snippet))
            except SearchError as e:
                logger.warning("Search disabled or failed: %s", e)
                break
    except Exception as exc:
        logger.exception("Error during search for %s: %s", company.name, exc)

    # Fetch and clean text for each document
    context_parts: List[str] = []
    for idx, (url, title, snippet) in enumerate(documents[:3]):  # Limit to 3 docs
        try:
            async with httpx.AsyncClient(timeout=10) as client:  # Reduced timeout
                resp = await client.get(url, headers={"User-Agent": "CompetitorResearchBot/1.0"})
                if resp.status_code == 200 and "text" in resp.headers.get("content-type", ""):
                    import re
                    from html import unescape
                    html = resp.text
                    html = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.DOTALL | re.IGNORECASE)
                    html = re.sub(r"<style[^>]*>.*?</style>", " ", html, flags=re.DOTALL | re.IGNORECASE)
                    text = re.sub(r"<[^>]+>", " ", html)
                    text = unescape(text)
                    text = re.sub(r"\s+", " ", text)
                    plain = text.strip()[:1500]  # Reduced from 3000
                else:
                    plain = snippet or ""
        except Exception as exc:
            logger.debug("Failed to fetch %s: %s", url, exc)
            plain = snippet or ""
        
        # Persist source document
        doc = SourceDocument(
            company_id=company.id,
            url=url,
            title=title,
            snippet=snippet,
            full_text=plain,
            source_type="website",
            relevance_score=None,
            published_at=None,
        )
        db.add(doc)
        context_parts.append(plain)
    
    await db.commit()

    # Compose prompt for LLM
    context_text = "\n\n".join(context_parts)[:4000]  # Reduced from 8000
    
    system_prompt = (
        "You are an expert market analyst for EdTech and LMS companies. "
        "Using the provided context, produce a JSON object describing the company. "
        "Required keys: name, website, segment, category, region, size_bucket, description, "
        "background, products, target_segments, pricing_model, market_position, strengths, "
        "risks, has_ai_features, compliance_tags. "
        "For list fields (products, target_segments, pricing_model, strengths, risks, compliance_tags), "
        "provide arrays of strings. "
        "Always include all keys. If information is unavailable, use null or an empty array. "
        "has_ai_features should be a boolean. "
        "Do not wrap the JSON in markdown or code blocks."
    )
    
    user_prompt = (
        f"Context:\n{context_text}\n\n"
        f"Company name: {company.name}. Website: {company.website or 'unknown'}. "
        "Return the JSON profile."
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    
    try:
        raw = await generate(messages, model=settings.LLM_MODEL, max_tokens=2000)
        
        # Clean up response
        raw = raw.strip()
        if raw.startswith("```json"):
            raw = raw[7:]
        if raw.startswith("```"):
            raw = raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()
        
        logger.info("Profile response for %s: %s", company.name, raw[:200])
        
        profile = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse profile JSON for %s: %s. Raw: %s", company.name, exc, raw[:500])
        profile = {}
    except Exception as exc:
        logger.exception("Error generating profile for %s: %s", company.name, exc)
        profile = {}
    
    # Update company fields
    def list_to_json(value):
        """Convert list to JSON string, or return original if not a list."""
        if isinstance(value, list):
            return json.dumps(value)
        elif isinstance(value, str):
            return value
        return None
    
    company.website = profile.get("website") or company.website
    company.segment = profile.get("segment") or company.segment
    company.category = profile.get("category") or company.category
    company.region = profile.get("region") or company.region
    company.size_bucket = profile.get("size_bucket") or company.size_bucket
    company.description = profile.get("description") or company.description
    company.background = profile.get("background") or company.background
    company.products = list_to_json(profile.get("products")) or company.products
    company.target_segments = list_to_json(profile.get("target_segments")) or company.target_segments
    company.pricing_model = list_to_json(profile.get("pricing_model")) or company.pricing_model
    company.market_position = profile.get("market_position") or company.market_position
    company.strengths = list_to_json(profile.get("strengths")) or company.strengths
    company.risks = list_to_json(profile.get("risks")) or company.risks
    company.has_ai_features = bool(profile.get("has_ai_features", company.has_ai_features))
    company.compliance_tags = list_to_json(profile.get("compliance_tags")) or company.compliance_tags
    company.last_updated = datetime.utcnow()
    
    await db.commit()
    logger.info("Successfully updated profile for: %s", company.name)



async def refresh_company(company_id: int, db: AsyncSession) -> None:
    """Refresh the profile for a specific company.

    Args:
        company_id: Primary key of the company to refresh.
        db: Database session.

    Raises:
        ValueError: If the company is not found.
    """
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalars().first()
    if not company:
        raise ValueError("Company not found")
    await profile_company(company, db)


async def get_stats_overview(db: AsyncSession) -> StatsOverviewResponse:
    """Compute high level statistics for charting.

    Returns:
        ``StatsOverviewResponse`` aggregating companies by category, region,
        pricing model and AI features.
    """
    buckets = {
        "by_category": [],
        "by_region": [],
        "pricing_models": [],
    }
    # Aggregations using SQL
    # Category
    result = await db.execute(select(Company.category, func.count()).group_by(Company.category))
    buckets["by_category"] = [StatsBucket(label=row[0] or "unknown", count=row[1]) for row in result.all()]
    # Region
    result = await db.execute(select(Company.region, func.count()).group_by(Company.region))
    buckets["by_region"] = [StatsBucket(label=row[0] or "unknown", count=row[1]) for row in result.all()]
    # Pricing model: explode lists encoded as JSON or comma separated
    result = await db.execute(select(Company.pricing_model))
    pricing_counts: Dict[str, int] = {}
    for row in result.scalars().all():
        if not row:
            pricing_counts.setdefault("unknown", 0)
            pricing_counts["unknown"] += 1
            continue
        value = row
        try:
            items = json.loads(value)
            if isinstance(items, list):
                for item in items:
                    pricing_counts.setdefault(item, 0)
                    pricing_counts[item] += 1
            else:
                pricing_counts.setdefault(str(items), 0)
                pricing_counts[str(items)] += 1
        except Exception:
            # comma separated fallback
            for part in value.split(","):
                part = part.strip()
                pricing_counts.setdefault(part or "unknown", 0)
                pricing_counts[part or "unknown"] += 1
    buckets["pricing_models"] = [StatsBucket(label=k, count=v) for k, v in pricing_counts.items()]
    # AI features counts
    result = await db.execute(select(Company.has_ai_features, func.count()).group_by(Company.has_ai_features))
    ai_counts: Dict[str, int] = {}
    for has_ai, count in result.all():
        key = "with_ai" if has_ai else "without_ai"
        ai_counts[key] = count
    return StatsOverviewResponse(
        by_category=buckets["by_category"],
        by_region=buckets["by_region"],
        pricing_models=buckets["pricing_models"],
        ai_features=ai_counts,
    )


async def compare_companies(company_ids: List[int], db: AsyncSession) -> CompanyCompareResponse:
    """Generate comparative insights across multiple companies.

    This function fetches company profiles and asks the language model to
    summarise common strengths, key differentiators and opportunity gaps.

    Args:
        company_ids: List of company primary keys.
        db: Database session.

    Returns:
        ``CompanyCompareResponse`` with structured insights.
    """
    if not company_ids:
        return CompanyCompareResponse()
    result = await db.execute(select(Company).where(Company.id.in_(company_ids)))
    companies = result.scalars().all()
    if not companies:
        return CompanyCompareResponse()
    # Compose context summarising each company
    lines: List[str] = []
    for c in companies:
        strengths = []
        if c.strengths:
            try:
                strengths = json.loads(c.strengths)
            except Exception:
                strengths = [s.strip() for s in c.strengths.split(",") if s.strip()]
        risks = []
        if c.risks:
            try:
                risks = json.loads(c.risks)
            except Exception:
                risks = [s.strip() for s in c.risks.split(",") if s.strip()]
        lines.append(
            f"Company {c.id}: {c.name}\n"
            f"  Category: {c.category or 'unknown'}\n"
            f"  Strengths: {', '.join(strengths) or 'unknown'}\n"
            f"  Risks: {', '.join(risks) or 'unknown'}"
        )
    context = "\n\n".join(lines)
    # LLM prompt for comparison
    system_prompt = (
        "You are a market analyst. You will be given summaries of multiple companies. "
        "Identify strengths that are common across all companies, list key differentiators for each company, "
        "and suggest opportunity gaps in the market. Return a JSON object with keys: "
        "common_strengths (list of strings), key_differences (list of objects with 'company_id' and 'points'), "
        "and opportunity_gaps (list of strings). Do not wrap the JSON in markdown."
    )
    user_prompt = f"Company summaries:\n{context}\n\nReturn the JSON insights."
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    raw = await generate(messages, model=settings.LLM_MODEL)
    try:
        data = json.loads(raw)
        common_strengths = data.get("common_strengths") or []
        key_diffs_data = data.get("key_differences") or []
        gaps = data.get("opportunity_gaps") or []
        key_differences: List[CompanyComparison] = []
        for diff in key_diffs_data:
            cid = diff.get("company_id")
            points = diff.get("points") or []
            if cid:
                key_differences.append(CompanyComparison(company_id=int(cid), points=points))
    except Exception as exc:
        logger.error("Failed to parse comparison JSON: %s", exc)
        common_strengths, key_differences, gaps = [], [], []
    return CompanyCompareResponse(
        common_strengths=common_strengths,
        key_differences=key_differences,
        opportunity_gaps=gaps,
    )