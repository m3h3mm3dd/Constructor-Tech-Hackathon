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
    """Application settings loaded from environment variables or ``.env`` file."""

    # OpenAI API key used by the OpenAI SDK. Required for communicating
    # with the OpenAI API. Populate this in your ``.env`` file or as an
    # environment variable.
    OPENAI_API_KEY: str

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

    # Configuration for retrieval‑augmented generation (RAG).
    # URL for connecting to a vector database (e.g. Chroma, Weaviate). If not provided,
    # a local in-memory Chroma DB will be used.
    VECTOR_DB_URL: str | None = None
    # Name of the collection used to store document embeddings.
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