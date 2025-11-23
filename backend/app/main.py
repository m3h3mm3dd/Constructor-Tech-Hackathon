"""
Main entry point for the AI agent backend.

This module creates the FastAPI application, configures middlewares such as CORS,
and includes the API routers for different parts of the system. A simple health
check endpoint is also provided.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings

# Import API routers from the versioned API package. Each router encapsulates
# routes for a distinct area of the API: chat interactions, streaming, agent
# management, and administration.
from .api.v1 import (
    chat_routes,
    stream_routes,
    agent_routes,
    admin_routes,
    research_routes,
    session_routes,
)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured FastAPI application instance.
    """
    app = FastAPI(
        title="AI Agent Backend",
        version="0.1.0",
        description="Backend service for an AI agent powered by FastAPI and OpenAI",
    )

    # Configure CORS. This allows your frontend (running on a different origin)
    # to communicate with this backend. Origins can be configured via environment
    # variable CORS_ORIGINS in the .env file.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routers. Prefixes organize endpoints under versioned paths.
    app.include_router(chat_routes.router, prefix="/api/v1/chat", tags=["chat"])
    app.include_router(stream_routes.router, prefix="/api/v1/chat/stream", tags=["stream"])
    app.include_router(agent_routes.router, prefix="/api/v1/agents", tags=["agents"])
    app.include_router(admin_routes.router, prefix="/api/v1/admin", tags=["admin"])
    # Include the competitor research endpoints under /api/v1/research
    app.include_router(research_routes.router, prefix="/api/v1", tags=["research"])
    app.include_router(session_routes.router, prefix="/api/v1", tags=["research-sessions"])

    # Health check endpoint. Useful for Kubernetes probes or uptime monitoring.
    @app.get("/health")
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app


# Create the application instance when this module is imported. This pattern
# supports running via ``uvicorn backend.app.main:app``.
app = create_app()
