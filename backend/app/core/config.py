"""
Application configuration.
"""

import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    DB_URL: str = "sqlite+aiosqlite:///./scout.db"
    
    # Vector Database (if you're using one)
    VECTOR_COLLECTION: str = "default"
    
    # API Keys
    SEARCH_API_KEY: str = os.getenv("SEARCH_API_KEY", "")
    SEARCH_API_BASE_URL: str = "https://api.tavily.com"
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "test-api-key")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", OPENAI_API_KEY)
    LLM_MODEL: str = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")
    LLM_API_BASE: str = os.getenv("LLM_API_BASE", "https://api.groq.com/openai/v1")
    
    # Celery (FIXED: Use Redis instead of RabbitMQ)
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # Allow extra fields from .env


settings = Settings()
