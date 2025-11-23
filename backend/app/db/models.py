"""
ORM model definitions using SQLAlchemy.

Defines ``User``, ``ChatSession``, and ``Message`` tables. These models
are simplistic and can be extended with additional fields or relations.
"""

from datetime import datetime

import uuid
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, Float, JSON
from sqlalchemy.orm import relationship

from .base import Base


class User(Base):
    """User account model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    messages = relationship("Message", back_populates="user", cascade="all, delete-orphan")


class ChatSession(Base):
    """Chat session model representing a conversation between a user and the agent."""

    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="sessions")
    messages = relationship(
        "Message",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="Message.id",
    )


class Message(Base):
    """Individual chat message within a session."""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ChatSession", back_populates="messages")
    user = relationship("User", back_populates="messages")


# ---------------------------------------------------------------------------
# EdTech / LMS competitor model
#
# The Company model stores structured information about education technology
# and learning management system vendors. It is used by the competitor
# research automation to maintain a catalog of companies and their
# attributes. Each company entry stores basic identifying details plus
# normalized attributes extracted from public sources (e.g. Wikipedia or
# company websites). The fields are flexible free‑text columns to allow
# storing semi‑structured data as JSON strings or comma‑separated lists.
#
# Fields:
#   name            – The company or product name (unique).
#   website         – Primary website URL if known.
#   category        – Broad category (e.g. "LMS", "Assessment", "Analytics").
#   description     – Concise one‑paragraph summary.
#   products        – Comma separated list of notable products or offerings.
#   target_segments – Comma separated list of target customer segments.
#   pricing_model   – Free‑form text describing pricing / licensing model.
#   country         – Headquarter country (best effort).
#   size            – Approximate company size (employees or revenue band).
#   strengths       – Comma separated list of strengths / differentiators.
#   risks           – Comma separated list of limitations or risks.
#   sources         – Semicolon separated list of URLs used to compile data.
#   last_updated    – Timestamp of last profile update (defaults to now).
#
# Additional fields can be added as needed for more detailed profiling.

class Company(Base):
    """EdTech or LMS company profile used for structured competitor research.

    The Company table stores a normalised profile for each competitor. Most
    fields are strings or JSON encoded text because the data originates from
    unstructured sources. Where a value is unknown, null or the string
    ``"unknown"`` may be stored. The ``first_discovered`` timestamp
    reflects when the company was initially added to the system via a
    research job. ``last_updated`` records the last time a profiling
    pipeline successfully refreshed the row.
    """

    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    # Basic identification fields
    name = Column(String, unique=True, index=True, nullable=False)
    website = Column(String, nullable=True)
    # High‑level segmentation attributes
    segment = Column(String, nullable=True)  # e.g. "university LMS Europe"
    category = Column(String, nullable=True)  # e.g. "LMS", "MOOC", "Tutoring"
    region = Column(String, nullable=True)  # e.g. "global", "EU", "US"
    size_bucket = Column(String, nullable=True)  # "small", "mid", "large", or "unknown"
    # Descriptive fields
    description = Column(Text, nullable=True)
    background = Column(Text, nullable=True)  # founding year, HQ etc.
    products = Column(Text, nullable=True)  # JSON string or comma separated list
    target_segments = Column(Text, nullable=True)  # JSON string
    pricing_model = Column(Text, nullable=True)  # JSON string
    market_position = Column(Text, nullable=True)
    strengths = Column(Text, nullable=True)  # JSON string
    risks = Column(Text, nullable=True)  # JSON string
    has_ai_features = Column(Boolean, default=False)
    compliance_tags = Column(Text, nullable=True)  # JSON string
    # Timestamps
    last_updated = Column(DateTime, default=datetime.utcnow)
    first_discovered = Column(DateTime, default=datetime.utcnow)

    # Relationships
    documents = relationship(
        "SourceDocument",
        back_populates="company",
        cascade="all, delete-orphan",
    )


class SourceDocument(Base):
    """Store individual documents used during company profiling.

    Each row captures a single source (web page, article, blog post, etc.)
    that was fetched as part of the profiling pipeline. The text itself may
    be truncated to keep storage costs reasonable. ``relevance_score`` is a
    floating point number between 0 and 1 representing the heuristic
    relevance to the company (higher is better).
    """

    __tablename__ = "source_documents"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    url = Column(String, nullable=False)
    title = Column(String, nullable=True)
    snippet = Column(Text, nullable=True)
    full_text = Column(Text, nullable=True)
    source_type = Column(String, nullable=True)  # e.g. "website", "wikipedia", "article"
    relevance_score = Column(Float, nullable=True)  # 0–1 score indicating relevance
    published_at = Column(DateTime, nullable=True)

    company = relationship("Company", back_populates="documents")


class ResearchJob(Base):
    """Track long‑running research tasks initiated by the user.

    When a user starts a competitor research job for a given segment, a
    ResearchJob row is created. The pipeline updates the status and
    timestamps as it progresses. In case of errors, ``error_message``
    contains a human‑readable description of what went wrong.
    """

    __tablename__ = "research_jobs"

    id = Column(Integer, primary_key=True, index=True)
    segment = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    # Optionally you could add a relationship to discovered companies
    # via an association table to track which companies belong to which job.


# ---------------------------------------------------------------------------
# New session-centric schema for Scout jobs (sessions + logs + trends)
# ---------------------------------------------------------------------------


class ResearchSession(Base):
    """Market research session initiated by the user."""

    __tablename__ = "research_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    label = Column(String, nullable=False, index=True)  # what user typed
    segment = Column(String, nullable=True)
    status = Column(String, nullable=False, default="PENDING")  # PENDING/RUNNING/COMPLETED/FAILED
    max_companies = Column(Integer, nullable=True)
    companies_found = Column(Integer, nullable=False, default=0)
    charts = Column(JSON, nullable=True)  # precomputed chart datasets
    scoring_config = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    logs = relationship("ResearchSessionLog", back_populates="session", cascade="all, delete-orphan")
    companies = relationship("SessionCompany", back_populates="session", cascade="all, delete-orphan")
    trends = relationship("TrendAnalysis", back_populates="session", cascade="all, delete-orphan")


class ResearchSessionLog(Base):
    """Ordered log lines for a session, driving the terminal console UI."""

    __tablename__ = "research_session_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("research_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    ts = Column(DateTime, default=datetime.utcnow, index=True)
    level = Column(String, default="info")  # info/success/warning/error
    message = Column(Text, nullable=False)
    meta = Column(JSON, nullable=True)

    session = relationship("ResearchSession", back_populates="logs")


class SessionCompany(Base):
    """Company discovered as part of a research session."""

    __tablename__ = "session_companies"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("research_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    domain = Column(String, nullable=True)
    logo_url = Column(String, nullable=True)
    score = Column(Integer, nullable=True)
    status = Column(String, default="PENDING")  # PENDING/COMPLETE/FAILED
    data_reliability = Column(String, default="medium")
    last_verified_at = Column(DateTime, nullable=True)
    founded_year = Column(Integer, nullable=True)
    employees = Column(Integer, nullable=True)
    hq_city = Column(String, nullable=True)
    hq_country = Column(String, nullable=True)
    primary_tags = Column(JSON, nullable=True)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    profile = relationship("CompanyProfile", back_populates="company", uselist=False, cascade="all, delete-orphan")
    sources = relationship("CompanySource", back_populates="company", cascade="all, delete-orphan")
    session = relationship("ResearchSession", back_populates="companies")


class CompanyProfile(Base):
    """Detailed profile content for a company (LLM generated)."""

    __tablename__ = "company_profiles"

    company_id = Column(String, ForeignKey("session_companies.id", ondelete="CASCADE"), primary_key=True)
    summary = Column(Text, nullable=True)
    score_analysis = Column(Text, nullable=True)
    market_position = Column(Text, nullable=True)
    background = Column(Text, nullable=True)
    recent_developments = Column(Text, nullable=True)
    products_services = Column(Text, nullable=True)
    scale_reach = Column(Text, nullable=True)
    strategic_notes = Column(Text, nullable=True)

    company = relationship("SessionCompany", back_populates="profile")


class CompanySource(Base):
    """Sources underpinning a company profile."""

    __tablename__ = "company_sources"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(String, ForeignKey("session_companies.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(String, nullable=False)
    label = Column(String, nullable=True)
    source_type = Column(String, nullable=True)  # news, official_site, report

    company = relationship("SessionCompany", back_populates="sources")


class TrendAnalysis(Base):
    """Stored trend analysis for a session."""

    __tablename__ = "trend_analyses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("research_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    overview = Column(Text, nullable=True)
    bars = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ResearchSession", back_populates="trends")
