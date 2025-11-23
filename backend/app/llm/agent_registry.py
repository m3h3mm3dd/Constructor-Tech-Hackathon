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
AGENTS: Dict[str, AgentConfig] = {
    "base": AgentConfig(
        name="base",
        description="Base agent with a generic system prompt",
        prompt_file="base_system.txt",
        model="qwen/qwen2.5-7b-instruct:free",
        tools=[],
    ),
    "student": AgentConfig(
        name="student",
        description="Friendly study companion tailored for students",
        prompt_file="student_agent.txt",
        model="qwen/qwen2.5-7b-instruct:free",
        tools=[],
    ),
    "prof": AgentConfig(
        name="prof",
        description="Experienced professor with deep academic knowledge",
        prompt_file="prof_agent.txt",
        model="qwen/qwen2.5-7b-instruct:free",
        tools=[],
    ),
    # New agent for structured EdTech competitor research. This persona
    # specialises in discovering and profiling companies in the education
    # technology sector. It uses a dedicated system prompt (see
    # app/llm/prompts/market_agent.txt) and the same free OpenRouter model.
    "market": AgentConfig(
        name="market",
        description="Market research agent for EdTech and LMS competitor intelligence",
        prompt_file="market_agent.txt",
        model="qwen/qwen2.5-7b-instruct:free",
        tools=[],
    ),
}


def list_agents() -> Dict[str, AgentConfig]:
    """Return all registered agents as a mapping."""
    return AGENTS


def get_default_agent() -> AgentConfig:
    """Return the default agent configuration."""
    return AGENTS["base"]