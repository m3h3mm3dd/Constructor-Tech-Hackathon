"""
Configuration module for the AI agent backend.

This module defines a ``Settings`` class based on Pydantic's BaseSettings,
which reads environment variables from a ``.env`` file and exposes them to
the rest of the application. Using this configuration layer centralizes
environment-specific parameters such as API keys, database URLs, and CORS
origins. A cached accessor is provided for convenient global access to the
configuration.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables or ``.env`` file.

    The configuration centralises all environment variables required by the
    application. In addition to the existing OpenAI API key and database
    settings, keys for the language model and web search provider are
    declared here. These keys should be populated via a ``.env`` file in
    the project root or exported as environment variables in your runtime
    environment.
    """

    # OpenRouter / OpenAI compatible API key used by the OpenAI SDK. This key
    # is mandatory for calling the chat completion API. Do not hardcode
    # secrets in source code; instead populate this in your ``.env`` file or
    # environment.
    OPENAI_API_KEY: str

    # Name of the language model to use when generating content via the
    # ``openai`` client. Defaults to a small and inexpensive model but can be
    # overridden in the ``.env`` file. For example, to use GPT‑4 set
    # ``LLM_MODEL=openai/gpt-4-turbo".
    LLM_MODEL: str = "openai/gpt-4.1-mini"

    # API key for the external web search provider (SerpAPI, Tavily, etc.).
    # The discovery and profiling pipelines call a search API to find
    # relevant documents. This key must be provided by the user.
    SEARCH_API_KEY: str | None = None

    # Base URL for the web search API. Different providers expose different
    # endpoints; set this to the root URL of your chosen provider. When
    # ``SEARCH_API_BASE_URL`` is not set, the search service will raise
    # informative errors instead of attempting any network calls.
    SEARCH_API_BASE_URL: str | None = None

    # Database connection URL. Defaults to a local SQLite database for
    # development. For production use, override with a PostgreSQL URL.
    DB_URL: str = "sqlite+aiosqlite:///./test.db"

    # Comma-separated list of origins allowed by CORS. Wildcards are
    # accepted. See FastAPI documentation for details on CORS configuration.
    CORS_ORIGINS: List[str] = ["*"]

    # Redis connection URL used by Celery for the broker and result backend.
    # Example: "redis://localhost:6379/0"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery broker URL. Defaults to REDIS_URL. Override if using a different broker.
    CELERY_BROKER_URL: str | None = None

    # Celery result backend. Defaults to REDIS_URL. Override if using a different backend.
    CELERY_RESULT_BACKEND: str | None = None

    # Configuration for retrieval‑augmented generation (RAG). These values are
    # unused in the competitor research agent but left here to avoid
    # breaking existing deployments. Ignore or remove if not needed.
    VECTOR_DB_URL: str | None = None
    VECTOR_COLLECTION: str = "default"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    """Lazily load settings to avoid re-reading environment variables.

    Returns:
        Settings: A cached Settings instance.
    """
    return Settings()


# Instantiate settings once for global use. Downstream modules can import
# ``settings`` directly instead of calling ``get_settings()`` repeatedly.
settings = get_settings()