"""
Registry of available agents.

This module defines a mapping of agent names to their configurations. Each
agent includes a name, description, prompt file path, model, and list of
allowed tools. A convenience function is provided to retrieve the default
agent.
"""

from typing import Dict

from ..schemas.agent import AgentConfig


# Define available agents. When adding a new agent, ensure the prompt file
# exists in ``app/llm/prompts`` and list any tools the agent may use.
# Register the available agents.  Each agent has a name, description,
# associated system prompt file, model identifier and allowed tools.  The
# default model is ``openai/gpt-oss-20b:free`` which is hosted by
# OpenRouter.  Tools are disabled by default because the free model
# does not support function calling; when using a paid model you can
# populate the ``tools`` list with names corresponding to functions in
# ``app/llm/tools``.
AGENTS: Dict[str, AgentConfig] = {
    "base": AgentConfig(
        name="base",
        description="Base agent with a generic system prompt",
        prompt_file="base_system.txt",
        model="openai/gpt-4o-mini",
        tools=[],
    ),
    "student": AgentConfig(
        name="student",
        description="Friendly study companion tailored for students",
        prompt_file="student_agent.txt",
        model="openai/gpt-4o-mini",
        tools=[],
    ),
    "prof": AgentConfig(
        name="prof",
        description="Experienced professor with deep academic knowledge",
        prompt_file="prof_agent.txt",
        model="openai/gpt-4o-mini",
        tools=[],
    ),
}


def list_agents() -> Dict[str, AgentConfig]:
    """Return all registered agents as a mapping."""
    return AGENTS


def get_default_agent() -> AgentConfig:
    """Return the default agent configuration."""
    return AGENTS["base"]