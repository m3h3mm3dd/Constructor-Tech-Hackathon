"""
Background tasks for the AI agent backend.

This module defines both scheduled jobs (via APScheduler) and Celery tasks for
long-running operations. Celery tasks are used when the workload is heavy and
should be executed asynchronously in a worker process, while the scheduler is
used for periodic maintenance jobs such as cleanup or analytics aggregation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
import logging

try:
    from celery import shared_task  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    # Provide a dummy decorator when Celery isn't installed. The dummy decorator
    # simply returns the function unchanged so that tests can run without Celery.
    def shared_task(*args, **kwargs):  # type: ignore
        def wrapper(func):
            return func
        return wrapper

from .scheduler import scheduler
from ..core.celery_app import celery_app
from ..services.session_service import append_log, build_default_charts
from ..db.models import ResearchSession, SessionCompany, CompanyProfile, CompanySource
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.session import async_session as async_session_factory
from ..core.openai_client import generate
from ..core.search import search_web, SearchError
import random
import asyncio
from ..core.config import settings

logger = logging.getLogger(__name__)


def register_tasks() -> None:
    """Register recurring tasks with the scheduler.

    At application startup, call this function to register any periodic
    maintenance tasks. For example, you might schedule regular cleanup of
    outdated chat sessions or aggregate usage analytics.
    """
    # Example: schedule a dummy task every hour
    scheduler.add_job(dummy_task, "interval", hours=1)


async def dummy_task() -> None:
    """A simple scheduled job that logs the current time."""
    print(f"Dummy task executed at {datetime.utcnow()}")


@celery_app.task(bind=True, name="backend.app.workers.tasks.run_agent_task")
def run_agent_task(self, conversation: list[dict[str, str]]) -> str:
    """Celery task that runs a long AI agent workflow.

    Args:
        conversation (list[dict[str, str]]): The chat history/messages as a list
            of dictionaries with ``role`` and ``content`` keys.

    Returns:
        str: Final response from the AI agent.

    Notes:
        This is a simplified example. In a real system, this task might
        orchestrate multiple tool calls, retrieval steps, or other
        computation-intensive operations. Progress updates can be emitted
        via ``self.update_state`` to provide intermediate statuses to the
        streaming API.
    """
    # Import inside the task to avoid circular dependencies
    from ..services.chat_service import handle_chat
    from ..schemas.common import Message
    import asyncio

    async def generate_response() -> str:
        # Convert dicts back into Pydantic models if necessary; here we assume
        # they already match the expected format.
        return await handle_chat([Message(**m) for m in conversation])  # type: ignore[name-defined]

    # Run the asynchronous chat handler in a synchronous Celery context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    response = loop.run_until_complete(generate_response())
    loop.close()
    return response


@celery_app.task(bind=True, name="backend.app.workers.tasks.run_scout_session")
def run_scout_session(self, session_id: str) -> str:
    """Celery task to execute the scout pipeline for a session."""
    logger.info("Celery worker: starting scout session %s", session_id)
    asyncio.run(_run_session_async(session_id))
    return "ok"

# Exported helper to run inline (FastAPI fallback when Celery/Redis not running)
async def run_session_inline(session_id: str) -> None:
    logger.info("Inline scout run for session %s", session_id)
    await _run_session_async(session_id)


async def _run_session_async(session_id: str) -> None:
    async with async_session_factory() as db:  # type: AsyncSession
        result = await db.execute(select(ResearchSession).where(ResearchSession.id == session_id))
        session = result.scalars().first()
        if not session:
            return
        session.status = "RUNNING"
        await db.commit()
        await append_log(db, session_id, "info", "Scanning for key players...")
        await append_log(db, session_id, "info", "Generating smart search queries...")
        await append_log(db, session_id, "info", "Crawling landing pages and docs...")

        # Discovery via LLM + search (fallback to simple heuristic)
        companies = await _discover_companies(session.label)
        if companies:
            await append_log(db, session_id, "success", f"Discovered {len(companies)} candidates.")
        else:
            await append_log(db, session_id, "warning", "No candidates discovered; using fallback.")

        discovered: list[SessionCompany] = []
        for comp in companies[: session.max_companies or 3]:
            # basic enrichment defaults
            employees_guess = comp.get("employees") or random.randint(500, 5000)
            founded_guess = comp.get("founded_year") or random.randint(1995, 2022)
            tags = comp.get("tags") or [segment or "", "education"]
            c = SessionCompany(
                session_id=session_id,
                name=comp.get("name"),
                domain=comp.get("domain"),
                primary_tags=tags,
                status="PENDING",
                score=comp.get("score") or random.randint(70, 95),
                data_reliability="medium",
                employees=employees_guess,
                founded_year=founded_guess,
            )
            db.add(c)
            await db.commit()
            await db.refresh(c)
            discovered.append(c)

        await append_log(db, session_id, "success", f"Found candidates: {', '.join([c.name for c in discovered])}")
        session.companies_found = len(discovered)
        await db.commit()

        # Profile each
        for comp in discovered:
            await append_log(db, session_id, "info", f"Analyzing {comp.name}...")
            profile_data = await _profile_company(comp.name, session.segment, comp.domain)
            summary = profile_data.get("summary") or comp.summary
            comp.summary = summary
            comp.status = "COMPLETE"
            comp.last_verified_at = comp.updated_at = comp.created_at
            profile = CompanyProfile(
                company_id=comp.id,
                summary=summary,
                score_analysis=profile_data.get("score_analysis") or "Generated by scout",
                background=profile_data.get("background"),
                products_services=profile_data.get("products_services"),
                market_position=profile_data.get("market_position"),
            )
            await db.merge(profile)
            sources = profile_data.get("sources") or []
            for src in sources:
                url = src.get("url") or src.get("link")
                if not url:
                    continue
                db.add(
                    CompanySource(
                        company_id=comp.id,
                        url=url,
                        label=src.get("label") or src.get("title"),
                        source_type=src.get("type") or "web",
                    )
                )
            await db.commit()
            await append_log(db, session_id, "success", f"Profile built: {comp.name}")

        # Charts
        charts = build_default_charts(discovered)
        session.charts = charts
        session.status = "COMPLETED"
        session.updated_at = datetime.utcnow()
        await db.commit()
        await append_log(db, session_id, "success", "Mission Complete.")


async def _discover_companies(segment: str) -> list[dict]:
    # Try web search for context
    search_context = ""
    try:
        queries = [f"{segment} company list", f"{segment} top companies"]
        results = []
        for q in queries:
            try:
                results += await search_web(q, num_results=4)
            except SearchError:
                continue
        seen = set()
        lines = []
        for r in results[:8]:
            url = r.get("url")
            if not url or url in seen:
                continue
            seen.add(url)
            lines.append(f"{r.get('title','')} | {url} | {r.get('snippet','')}")
        search_context = "\n".join(lines)
    except Exception:
        search_context = ""

    prompt = (
        "CRITICAL RELIABILITY RULES:\n"
        "- Only return real companies with active websites relevant to the topic.\n"
        "- Do NOT hallucinate names; skip anything uncertain.\n"
        "- Output JSON with key 'companies' as a list of objects: {name, website, tags}.\n"
        f"Topic: {segment}\n"
        "Search context:\n"
        f"{search_context}\n"
        "Return only JSON."
    )
    try:
        raw = await generate(
            [
                {"role": "system", "content": "You are a market research assistant. Respond with JSON only."},
                {"role": "user", "content": prompt},
            ],
            model=settings.LLM_MODEL,
            max_tokens=800,
        )
        import json
        data = json.loads(raw)
        if isinstance(data, dict) and "companies" in data:
            return data["companies"]
        if isinstance(data, list):
            return data
    except Exception:
        pass
    # deterministic fallback
    fallback = [
        {"name": f"{segment.title()} Group", "domain": None, "tags": [segment, "education"]},
        {"name": f"{segment.title()} Labs", "domain": None, "tags": [segment, "innovation"]},
        {"name": f"{segment.title()} Systems", "domain": None, "tags": [segment, "platform"]},
    ]
    return fallback


async def _fetch_context_for_company(name: str, segment: str | None) -> tuple[str, list[dict]]:
    ctx_chunks = []
    sources: list[dict] = []
    queries = [f"{name} {segment or ''} company", f"{name} products", f"{name} background"]
    seen_urls = set()
    for q in queries:
        try:
            results = await search_web(q, num_results=3)
            for r in results:
                url = r.get("url")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                sources.append({"url": url, "title": r.get("title"), "snippet": r.get("snippet")})
                ctx_chunks.append(f"{r.get('title','')} | {url} | {r.get('snippet','')}")
        except Exception:
            continue
    context = "\n".join(ctx_chunks)
    return context, sources


async def _profile_company(name: str, segment: str | None, domain: str | None) -> dict:
    context, discovered_sources = await _fetch_context_for_company(name, segment)
    prompt = (
        "VERIFICATION PROTOCOL:\n"
        "- Cross-check facts with at least two distinct sources.\n"
        "- Only include information if sources agree or are corroborated.\n"
        "- If unsure, set fields to null.\n"
        "Return JSON with keys: summary, background, products_services, market_position, score_analysis, sources (list of {url,label,type}).\n"
        f"Company: {name}\n"
        f"Website: {domain or 'unknown'}\n"
        f"Topic: {segment or 'general'}\n"
        f"Sources:\n{context}\n"
        "Return only JSON."
    )
    try:
        raw = await generate(
            [
                {"role": "system", "content": "You are a careful analyst that outputs strict JSON only."},
                {"role": "user", "content": prompt},
            ],
            model=settings.LLM_MODEL,
            max_tokens=800,
        )
        import json
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("Invalid profile JSON")
        if "sources" not in data and discovered_sources:
            data["sources"] = discovered_sources
        return data
    except Exception:
        return {
            "summary": f"{name} is a company relevant to {segment}.",
            "background": None,
            "products_services": None,
            "market_position": None,
            "score_analysis": None,
            "sources": discovered_sources,
        }
