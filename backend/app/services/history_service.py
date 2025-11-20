"""
History service stub.

This service manages chat histories. In this simplified implementation,
histories are stored in an in-memory dictionary keyed by session ID. For
a production deployment you might back this with a database or Redis to
support persistence and scaling.
"""

from typing import List, Dict

from ..schemas.common import Message


class HistoryService:
    """Manage conversation histories for chat sessions."""

    def __init__(self) -> None:
        # Map session ID to list of messages
        self._store: Dict[str, List[Message]] = {}

    def add_message(self, session_id: str, message: Message) -> None:
        """Append a message to the history for a given session."""
        self._store.setdefault(session_id, []).append(message)

    def get_history(self, session_id: str) -> List[Message]:
        """Retrieve the conversation history for a session."""
        return list(self._store.get(session_id, []))