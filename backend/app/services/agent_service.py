"""
Agent service layer.

This module mediates access to the agent registry and provides basic CRUD
operations for agents. In this simplified example, agents are stored in
memory. Persisting agent definitions to a database or configuration store
would be a straightforward extension.
"""

from typing import Dict, Iterable, Optional

from ..llm.agent_registry import AGENTS
from ..schemas.agent import AgentConfig


def list_agents() -> Iterable[AgentConfig]:
    """Return an iterable of all agent configurations."""
    return AGENTS.values()


def get_agent(name: str) -> Optional[AgentConfig]:
    """Fetch a single agent configuration by name."""
    return AGENTS.get(name)


def update_agent(name: str, config: AgentConfig) -> AgentConfig:
    """Replace an existing agent configuration.

    Args:
        name (str): Name of the agent to update.
        config (AgentConfig): New configuration to apply.

    Returns:
        AgentConfig: The updated agent configuration.
    """
    AGENTS[name] = config
    return config