"""
Common schema definitions.

Defines basic models used throughout the API for chat messages and tool calls.
Pydantic is used to enforce type validation and JSON serialization.
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class Message(BaseModel):
    """Represents a single chat message within a conversation."""

    role: str = Field(..., description="The role of the message sender, e.g. 'user' or 'assistant'.")
    content: str = Field(..., description="The text content of the message.")
    name: Optional[str] = Field(None, description="Optional name of the message sender.")


class ToolCall(BaseModel):
    """Represents a request to call an external tool with arguments."""

    name: str = Field(..., description="Name of the tool to call.")
    arguments: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arguments to pass to the tool when invoked.",
    )