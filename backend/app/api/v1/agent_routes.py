"""
Agent management API routes.

Provides endpoints to list available agents, retrieve an individual agent,
and update agent configurations. Agents are defined in the ``llm``
module and exposed via the agent service layer.
"""

from fastapi import APIRouter, Depends, HTTPException, Path

from ...core.security import get_api_key
from ...schemas.agent import AgentListResponse, AgentConfig
from ...services.agent_service import list_agents, get_agent, update_agent


router = APIRouter()


@router.get("/", response_model=AgentListResponse)
async def list_available_agents(api_key: str = Depends(get_api_key)) -> AgentListResponse:
    """Return a list of all configured agents."""
    agents = list_agents()
    return AgentListResponse(agents=agents)


@router.get("/{name}", response_model=AgentConfig)
async def read_agent(
    name: str = Path(..., description="The unique name of the agent"),
    api_key: str = Depends(get_api_key),
) -> AgentConfig:
    """Retrieve a single agent's configuration by name."""
    agent = get_agent(name)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.put("/{name}", response_model=AgentConfig)
async def update_agent_endpoint(
    name: str = Path(..., description="The unique name of the agent"),
    config: AgentConfig | None = None,
    api_key: str = Depends(get_api_key),
) -> AgentConfig:
    """Update an existing agent's configuration.

    Note:
        This endpoint accepts an entire ``AgentConfig`` payload to replace the
        existing configuration. Partial updates are not yet supported.
    """
    if config is None or config.name != name:
        raise HTTPException(status_code=400, detail="Agent name mismatch")
    updated = update_agent(name, config)
    return updated