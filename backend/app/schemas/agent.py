"""
Agent schema definitions.

An agent represents a distinct persona or configuration for the AI model,
including its name, description, associated prompt file, and allowed tools.
This schema is used in the agent management API and services.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    """Configuration for a single agent."""

    name: str = Field(..., description="Unique identifier for the agent.")
    description: str = Field(..., description="Human-readable description of the agent.")
    prompt_file: str = Field(
        ..., description="Relative path to the prompt file used to prime the model."
    )
    model: str = Field("gpt-5.1", description="Model name to use for this agent.")
    tools: Optional[List[str]] = Field(
        default=None,
        description="List of tool names the agent is allowed to invoke.",
    )


class AgentListResponse(BaseModel):
    """Response model for listing multiple agents."""

    agents: List[AgentConfig]