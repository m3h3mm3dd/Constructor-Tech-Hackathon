"""
Tool service layer.

This module provides a single entry point for invoking tools based on
their name. It isolates the rest of the codebase from the internal
structure of the tool modules.
"""

from typing import Any, Dict

from ..llm.tools import calendar_tool, faq_tool, search_tool


async def call_tool(name: str, args: Dict[str, Any]) -> Any:
    """Invoke a tool by name.

    Args:
        name (str): Name of the tool to call.
        args (Dict[str, Any]): Arguments to pass to the tool.

    Returns:
        Any: Result returned by the tool.

    Raises:
        ValueError: If an unknown tool name is provided.
    """
    if name == "calendar":
        return await calendar_tool.run(args)
    if name == "faq":
        return await faq_tool.run(args)
    if name == "search":
        return await search_tool.run(args)
    raise ValueError(f"Unknown tool: {name}")