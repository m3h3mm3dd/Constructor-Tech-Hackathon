"""
User schema definitions.

Simple Pydantic models representing a user within the system. These can be
expanded with additional fields such as password hashes, roles, or
profile information as needed.
"""

from pydantic import BaseModel, Field


class User(BaseModel):
    """Represents a user account."""

    id: int = Field(..., description="Unique identifier for the user.")
    email: str = Field(..., description="User's email address.")
    is_active: bool = Field(True, description="Whether the user account is active.")