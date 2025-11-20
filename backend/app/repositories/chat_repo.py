"""
Chat session repository functions.

Handles creation of chat sessions and retrieval of messages. Storing
repository functions here decouples low-level database operations from
service logic.
"""

from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import ChatSession, Message


async def create_chat_session(db: AsyncSession, user_id: int) -> ChatSession:
    """Create and persist a new chat session for a user."""
    session = ChatSession(user_id=user_id)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def add_message(
    db: AsyncSession, session_id: int, user_id: int | None, role: str, content: str
) -> Message:
    """Add a message to a chat session."""
    msg = Message(session_id=session_id, user_id=user_id, role=role, content=content)
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


async def get_session_messages(db: AsyncSession, session_id: int) -> List[Message]:
    """Return all messages for a chat session, ordered by creation."""
    result = await db.execute(select(Message).where(Message.session_id == session_id).order_by(Message.id))
    return result.scalars().all()