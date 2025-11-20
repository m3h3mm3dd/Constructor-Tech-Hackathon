"""
Schemas for chat requests and responses.

The ``ChatRequest`` model expects a list of ``Message`` objects, while
``ChatResponse`` contains the agent's textual reply. These schemas are
shared between the API layer and the service layer for type safety and
validation.
"""

from typing import List

from pydantic import BaseModel, Field

from .common import Message


class ChatRequest(BaseModel):
    """Request payload for sending a chat to the AI agent."""

    messages: List[Message] = Field(
        ..., description="Ordered list of messages representing the conversation so far."
    )


class ChatResponse(BaseModel):
    """Response payload containing the agent's reply."""

    reply: str = Field(..., description="The agent's generated reply text.")