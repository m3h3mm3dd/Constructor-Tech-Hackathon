"""
Celery tasks for background job processing.
"""

import asyncio
import json
import logging
import re
from datetime import datetime
from html import unescape
from typing import Any, Dict, List, Optional

import httpx
from celery import shared_task
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.llm import LLMService
from ..core.search import SearchService
from ..db.models import (
    CompanyProfile,
    CompanySource,
    ResearchSession,
    ResearchSessionLog,
    SessionCompany,
)
from ..db.session import async_session

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="backend.app.workers.tasks.run_agent_task")
def run_agent_task(self, query: str, chat_id: str) -> Dict[str, Any]:
    """Run agent research task."""
    logger.info(f"Running agent task for chat {chat_id}")
    return {"status": "completed", "query": query}


@shared_task(bind=True, name="backend.app.workers.tasks.run_scout_session")
def run_scout_session(self, session_id: str) -> Dict[str, Any]:
    """Run full scout research session."""
    logger.info(f"Celery worker: starting scout session {session_id}")
    
    try:
        # Run async work
        asyncio.run(_run_session_async(session_id))
        return {"status": "completed", "session_id": session_id}
    except Exception as e:
        logger.exception(f"Scout session {session_id} failed: {e}")
        # Update session status to failed
        asyncio.run(_mark_session_failed(session_id, str(e)))
        raise


async def run_session_inline(session_id: str):
    """Run session inline (for testing without Celery)."""
    try:
        await _run_session_async(session_id)
    except Exception as e:
        logger.exception(f"Inline session {session_id} failed: {e}")
        await _mark_session_failed(session_id, str(e))
        raise


async def _run_session_async(session_id: str):
    """Core async logic for running a scout session."""
    async with async_session() as db:
        # Get session
        result = await db.execute(select(ResearchSession).where(ResearchSession.id == session_id))
        session = result.scalar_one_or_none()
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Update to RUNNING
        session.status = "RUNNING"
        await db.commit()
        
        # Initialize services
        search_service = SearchService(api_key=settings.SEARCH_API_KEY)
        llm_service = LLMService(api_key=settings.LLM_API_KEY, model=settings.LLM_MODEL)
        
        try:
            # Step 1: Discover companies
            await _add_log(db, session_id, "Starting company discovery...")
            companies = await _discover_companies_reliably(
                segment=session.segment,
                max_companies=session.max_companies or 5,
                search_service=search_service,
                llm_service=llm_service
            )
            
            await _add_log(db, session_id, f"Discovered {len(companies)} companies: {[c['name'] for c in companies]}")
            
            # Step 2: Save discovered companies
            session.companies_found = len(companies)
            for comp_data in companies:
                comp = SessionCompany(
                    session_id=session_id,
                    name=comp_data.get("name", "Unknown"),
                    domain=comp_data.get("domain", ""),
                    primary_tags=comp_data.get("tags", []),
                )
                db.add(comp)
            
            await db.commit()
            
            # Step 3: Deep profile each company
            result = await db.execute(
                select(SessionCompany).where(SessionCompany.session_id == session_id)
            )
            companies_to_profile = result.scalars().all()
            
            for comp in companies_to_profile:
                try:
                    await _add_log(db, session_id, f"Deep research on {comp.name}...")
                    
                    profile_data = await _deep_profile_company(
                        company_name=comp.name,
                        company_domain=comp.domain,
                        segment=session.segment,
                        search_service=search_service,
                        llm_service=llm_service
                    )
                    
                    # Persist the detailed profile content
                    profile = CompanyProfile(
                        company_id=comp.id,
                        summary=_safe_text(profile_data.get("summary")),
                        score_analysis=_safe_text(profile_data.get("score_analysis")),
                        market_position=_safe_text(profile_data.get("market_position")),
                        background=_safe_text(profile_data.get("background")),
                        recent_developments=_safe_text(profile_data.get("recent_developments")),
                        products_services=_safe_text(profile_data.get("products_services")),
                        scale_reach=_safe_text(profile_data.get("scale_reach")),
                        strategic_notes=_safe_text(profile_data.get("strategic_notes")),
                    )
                    db.add(profile)

                    # Update high-level company fields stored on SessionCompany
                    comp.summary = profile.summary
                    comp.data_reliability = profile_data.get("data_reliability", "medium")
                    comp.last_verified_at = datetime.utcnow()
                    comp.status = "COMPLETE"
                    
                    # Add sources
                    for src in profile_data.get("sources", [])[:10]:  # Limit to 10 sources
                        source = CompanySource(
                            company_id=comp.id,
                            url=src.get("url", ""),
                            label=src.get("title", "Unknown"),
                            source_type=src.get("source_type") or None,
                        )
                        db.add(source)
                    
                    await db.commit()
                    await db.refresh(comp)
                    
                    await _add_log(db, session_id, f"✓ Profile complete: {comp.name}")
                    
                except Exception as e:
                    await db.rollback()  # Critical: rollback on error
                    logger.exception(f"Failed to profile {comp.name}: {e}")
                    await _add_log(db, session_id, f"✗ Failed to profile {comp.name}: {str(e)[:100]}")
                    continue
            
            # Step 4: Generate charts (placeholder)
            charts_data = {
                "segmentation": [],
                "scale": [],
                "performance": [],
                "evolution": []
            }
            session.charts = charts_data  # store as dict (JSON column)
            
            # Mark complete
            session.status = "COMPLETE"
            session.updated_at = datetime.utcnow()
            await db.commit()
            
            await _add_log(db, session_id, "✅ Research session complete!")
            
        except Exception as e:
            await db.rollback()
            logger.exception(f"Session {session_id} failed: {e}")
            session.status = "FAILED"
            await db.commit()
            await _add_log(db, session_id, f"❌ Session failed: {str(e)}")
            raise


async def _discover_companies_reliably(
    segment: str,
    max_companies: int,
    search_service: SearchService,
    llm_service: LLMService
) -> List[Dict[str, Any]]:
    """
    Discover companies using multi-query search + LLM validation.
    """
    # Multiple search queries
    queries = [
        f"{segment} companies list",
        f"top {segment} companies",
        f"{segment} market leaders",
        f"leading {segment} businesses"
    ]
    
    all_results = []
    for query in queries[:3]:  # Limit to 3 queries
        try:
            results = await search_service.search(query, num_results=10)
            all_results.extend(results)
            await asyncio.sleep(0.5)  # Rate limiting
        except Exception as e:
            logger.warning(f"Search failed for '{query}': {e}")
    
    # Build context
    context = "\n\n".join([
        f"Title: {r.get('title', '')}\nURL: {r.get('url', '')}\nContent: {r.get('content', '')[:300]}"
        for r in all_results[:15]
    ])
    
    # LLM extraction with strict instructions
    prompt = f"""Based ONLY on the search results below, extract a list of {max_companies} real companies in the "{segment}" segment.

CRITICAL RULES:
1. Only return companies that appear in the search results OR that you are 100% certain exist
2. Each company MUST have: name, domain (website URL), description
3. Do NOT invent or hallucinate companies
4. Return valid JSON array only

Search Results:
{context}

Return format:
[
  {{"name": "Company Name", "domain": "company.com", "description": "Brief description", "tags": ["tag1", "tag2"]}},
  ...
]

Return ONLY the JSON array, no markdown, no explanation."""
    
    try:
        response = await llm_service.generate(prompt, max_tokens=2000)
        
        # Clean response
        response_text = response.strip()
        response_text = re.sub(r'```json\s*', '', response_text)
        response_text = re.sub(r'```\s*$', '', response_text)
        response_text = response_text.strip()
        
        companies = json.loads(response_text)
        
        # Validate
        valid_companies = []
        for c in companies:
            if isinstance(c, dict) and "name" in c and "domain" in c:
                valid_companies.append(c)
        
        return valid_companies[:max_companies]
        
    except Exception as e:
        logger.error(f"LLM discovery failed: {e}")
        return []


async def _deep_profile_company(
    company_name: str,
    company_domain: str,
    segment: str,
    search_service: SearchService,
    llm_service: LLMService
) -> Dict[str, Any]:
    """
    Deep profile a single company with multi-source verification.
    Returns data with proper types for JSON serialization.
    """
    # Multi-angle searches
    search_queries = [
        f"{company_name} company profile",
        f"{company_name} products services",
        f"{company_name} background information"
    ]
    
    all_sources = []
    for query in search_queries:
        try:
            results = await search_service.search(query, num_results=5)
            all_sources.extend(results)
            await asyncio.sleep(0.3)
        except Exception as e:
            logger.warning(f"Search failed for {company_name}: {e}")
    
    # Fetch website content
    website_content = ""
    if company_domain:
        try:
            website_content = await _fetch_website_content(company_domain)
        except Exception as e:
            logger.warning(f"Failed to fetch website for {company_name}: {e}")
    
    # Build comprehensive context
    context = f"Company Website Content:\n{website_content}\n\n"
    context += "Search Results:\n" + "\n\n".join([
        f"Source {i+1}:\nTitle: {s.get('title', '')}\nURL: {s.get('url', '')}\nContent: {s.get('content', '')[:500]}"
        for i, s in enumerate(all_sources[:10])
    ])
    
    # LLM analysis with strict data structure
    prompt = f"""Analyze {company_name} based ONLY on the provided sources. Cross-reference facts across multiple sources.

Company: {company_name}
Segment: {segment}

Sources:
{context}

Provide a JSON response with this EXACT structure:
{{
  "summary": "150-word summary",
  "score_analysis": "Why this company scores well/poorly in the {segment} market",
  "market_position": "Market position in {segment} segment",
  "background": "Background as a STRING (founding info, history)",
  "recent_developments": "Recent developments as a STRING",
  "products_services": ["Product 1", "Product 2", "Product 3"],
  "scale_reach": "Scale and reach as a STRING (employee count, geographic presence)",
  "strategic_notes": "Strategic notes as a STRING",
  "data_reliability": "high|medium|low"
}}

IMPORTANT:
- background, recent_developments, scale_reach, strategic_notes should be PLAIN TEXT STRINGS, not objects
- products_services should be a simple array of strings
- Base analysis ONLY on provided sources
- Return ONLY valid JSON, no markdown"""
    
    try:
        response = await llm_service.generate(prompt, max_tokens=2000)
        
        # Clean response
        response_text = response.strip()
        response_text = re.sub(r'```json\s*', '', response_text)
        response_text = re.sub(r'```\s*$', '', response_text)
        response_text = response_text.strip()
        
        profile_data = json.loads(response_text)
        
        # Add sources
        profile_data["sources"] = [
            {"url": s.get("url", ""), "title": s.get("title", ""), "snippet": s.get("content", "")[:200], "relevance": 0.8}
            for s in all_sources[:10]
        ]
        
        # Ensure data reliability
        num_sources = len(all_sources)
        if num_sources >= 5:
            profile_data["data_reliability"] = "high"
        elif num_sources >= 3:
            profile_data["data_reliability"] = "medium"
        else:
            profile_data["data_reliability"] = "low"
        
        return profile_data
        
    except Exception as e:
        logger.error(f"LLM profiling failed for {company_name}: {e}")
        # Return minimal data
        return {
            "summary": f"Profile data unavailable for {company_name}",
            "score_analysis": "Insufficient data",
            "market_position": "Unknown",
            "background": "No background data available",
            "recent_developments": "No recent developments available",
            "products_services": [],
            "scale_reach": "Unknown",
            "strategic_notes": "Insufficient data for analysis",
            "data_reliability": "low",
            "sources": []
        }


def _safe_text(value: Any) -> str:
    """Convert arbitrary data to a safe string for text columns."""
    if value is None:
        return ""
    if isinstance(value, (str, int, float)):
        return str(value)
    try:
        return json.dumps(value, ensure_ascii=False)
    except Exception:
        return str(value)


async def _fetch_website_content(domain: str) -> str:
    """Fetch and clean website content."""
    url = domain if domain.startswith("http") else f"https://{domain}"
    
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
            )
            html = response.text
            
            # Remove scripts and styles
            html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
            html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
            html = re.sub(r'<[^>]+>', ' ', html)
            
            # Clean text
            text = unescape(html)
            text = re.sub(r'\s+', ' ', text)
            
            return text[:3000]  # Limit length
            
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return ""


async def _add_log(db: AsyncSession, session_id: str, message: str):
    """Add log entry to session."""
    log = ResearchSessionLog(
        session_id=session_id,
        message=message
    )
    db.add(log)
    await db.commit()
    logger.info(f"[{session_id}] {message}")


async def _mark_session_failed(session_id: str, error: str):
    """Mark session as failed."""
    async with async_session() as db:
        result = await db.execute(select(ResearchSession).where(ResearchSession.id == session_id))
        session = result.scalar_one_or_none()
        if session:
            session.status = "FAILED"
            session.updated_at = datetime.utcnow()
            await db.commit()
            await _add_log(db, session_id, f"Session failed: {error[:200]}")
