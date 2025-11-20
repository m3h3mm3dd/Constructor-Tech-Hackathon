"""
Tests for agent logic functions.
"""

from app.llm.agent_registry import list_agents, get_default_agent

def test_list_agents_returns_agents() -> None:
    agents = list(list_agents())
    assert len(agents) >= 1


def test_default_agent_is_base() -> None:
    default_agent = get_default_agent()
    assert default_agent.name == "base"
