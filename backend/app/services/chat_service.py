"""
Chat service implementation.

This module orchestrates chat interactions by assembling the conversation
messages, optionally invoking a planner to decide on tool calls, and
delegating to the OpenAI client for generating replies. It also exposes
a streaming variant for incremental responses.
"""

from typing import AsyncGenerator, List

from ..schemas.common import Message
from ..llm.agent_registry import get_default_agent
from ..llm.planner import plan
from ..llm.tools import calendar_tool, faq_tool, search_tool
from ..core.openai_client import generate, generate_stream


async def handle_chat(messages: List[Message]) -> str:
    """Handle a chat request and return the AI agent's reply.

    Args:
        messages (List[Message]): Ordered list of messages representing the conversation.

    Returns:
        str: The generated reply from the AI agent.
    """
    agent = get_default_agent()
    # Convert pydantic models to dictionaries expected by OpenAI API
    formatted = [m.dict(exclude_unset=True) for m in messages]

    # If RAG context is enabled and the last message comes from the user,
    # retrieve relevant context and inject it as a system message. This helps
    # ground the model’s responses in factual data. See DataCamp’s RAG
    # tutorial for more details on the retrieval workflow【438448550825859†L103-L139】.
    if messages and messages[-1].role == "user":
        try:
            from ..services.rag_service import retrieve_context  # type: ignore

            context_chunks = await retrieve_context(messages[-1].content, k=3)
            if context_chunks:
                context_text = "\n\n".join([chunk for chunk, _ in context_chunks])
                # Prepend context as a system message
                formatted.insert(
                    0,
                    {
                        "role": "system",
                        "content": f"Relevant context:\n{context_text}",
                    },
                )
        except Exception:
            # If RAG service isn't configured or fails, silently skip context injection
            pass

    # Plan which tool to use based on the conversation. If the planner
    # decides a tool call is required, execute it and append the result.
    tool_call = await plan(messages)
    if tool_call:
        name = tool_call.get("name")
        args = tool_call.get("arguments", {})
        if name == "calendar":
            result = await calendar_tool.run(args)
        elif name == "faq":
            result = await faq_tool.run(args)
        elif name == "search":
            result = await search_tool.run(args)
        else:
            result = {"error": f"Unknown tool {name}"}
        # Insert tool call result into the conversation. The format used here
        # depends on your prompt conventions.
        formatted.append({"role": "tool", "name": name, "content": str(result)})

    # Ask the language model for a reply.
    # Map tool names into the format expected by the Responses API. Each tool
    # definition should at minimum include its name and type. Since our
    # ``openai_client.generate`` helper accepts a list of arbitrary dicts,
    # converting the list of strings here keeps the agent config flexible.
    tool_defs = None
    if agent.tools:
        tool_defs = [{"type": "function", "name": name} for name in agent.tools]
    reply = await generate(formatted, model=agent.model, tools=tool_defs)
    return reply


async def stream_chat(messages: List[Message]) -> AsyncGenerator[str, None]:
    """Stream the AI agent's reply chunk by chunk.

    This implementation yields whitespace-separated tokens. Modify as needed
    to use actual streaming support from your LLM provider.

    Args:
        messages (List[Message]): Conversation messages.

    Yields:
        AsyncGenerator[str, None]: Chunks of the reply.
    """
    """Stream the AI agent's reply using the OpenAI Responses API.

    Instead of splitting a full response into tokens, call the
    ``generate_stream`` helper to yield chunks as they arrive from the
    model. This preserves any streaming support provided by the API and
    reduces latency for the end user.
    """
    agent = get_default_agent()
    formatted = [m.dict(exclude_unset=True) for m in messages]
    # Convert allowed tools to tool definitions
    tool_defs = None
    if agent.tools:
        tool_defs = [{"type": "function", "name": name} for name in agent.tools]
    async for chunk in generate_stream(formatted, model=agent.model, tools=tool_defs):
        yield chunk