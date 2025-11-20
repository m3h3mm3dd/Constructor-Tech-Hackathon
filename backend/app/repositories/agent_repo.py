"""
Agent repository stub.

Provides a persistence layer for agent configurations. This example uses
the in-memory registry defined in ``llm/agent_registry.py``. You can
extend this module to persist agents in a database.
"""

from typing import Iterable, Optional

from ..llm.agent_registry import AGENTS
from ..schemas.agent import AgentConfig


def list_agents() -> Iterable[AgentConfig]:
    return AGENTS.values()


def get_agent(name: str) -> Optional[AgentConfig]:
    return AGENTS.get(name)


def save_agent(config: AgentConfig) -> None:
    AGENTS[config.name] = config