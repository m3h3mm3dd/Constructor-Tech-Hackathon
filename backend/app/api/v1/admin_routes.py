"""
Administrative API routes.

These endpoints expose operational information useful for monitoring and
administration, such as usage statistics. Access is restricted via API
key. In a production system you may implement more sophisticated access
controls or separate the admin API entirely.
"""

from fastapi import APIRouter, Depends

from ...core.security import get_api_key
from ...services.analytics_service import get_usage_stats


router = APIRouter()


@router.get("/stats")
async def statistics(api_key: str = Depends(get_api_key)) -> dict:
    """Return usage statistics for the AI agent backend."""
    return await get_usage_stats()