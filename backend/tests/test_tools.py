"""
Tests for tool stubs.
"""

import asyncio

import pytest

from app.llm.tools import calendar_tool, faq_tool, search_tool

@pytest.mark.asyncio
async def test_calendar_tool_returns_empty_events():
    result = await calendar_tool.run({})
    assert "events" in result
    assert result["events"] == []

@pytest.mark.asyncio
async def test_faq_tool_returns_answer():
    result = await faq_tool.run({"question": "What is this?"})
    assert result["answer"]

@pytest.mark.asyncio
async def test_search_tool_returns_results_list():
    result = await search_tool.run({"query": "test"})
    assert "results" in result
    assert isinstance(result["results"], list)
