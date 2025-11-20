"""
Planner module stub.

A planner decides which tool (if any) to invoke based on the current
conversation. The simplest planner returns ``None`` indicating no tool
call. You can extend this logic to parse messages and determine whether
a calendar lookup, FAQ search, or web search is appropriate.
"""

from typing import List, Optional

from ..schemas.common import Message


async def plan(messages: List[Message]) -> Optional[dict]:
    """Decide which tool to call based on the conversation history.

    Args:
        messages (List[Message]): Ordered list of conversation messages.

    Returns:
        Optional[dict]: If a tool call is needed, return a dict with
            ``name`` and ``arguments`` keys. Otherwise, return None.
    """
    # TODO: implement intelligent tool planning based on message content.
    return None