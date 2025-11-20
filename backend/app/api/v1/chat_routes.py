"""
API routes for chat interactions.

This router exposes an endpoint for sending a list of messages to the AI
agent and receiving a reply. Authentication via API key is enforced at
route level. Additional endpoints (e.g., for chat history) can be added
here or organized in separate modules.
"""

from fastapi import APIRouter, Depends

from ...core.security import get_api_key
from ...schemas.chat import ChatRequest, ChatResponse
from ...services.chat_service import handle_chat


router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    api_key: str = Depends(get_api_key),
) -> ChatResponse:
    """Send a chat request to the AI agent and return its reply.

    Args:
        request (ChatRequest): Contains a list of message objects representing
            the conversation so far.
        api_key (str): Provided API key, validated via dependency.

    Returns:
        ChatResponse: The agent's reply encapsulated in a response model.
    """
    reply_text = await handle_chat(request.messages)
    return ChatResponse(reply=reply_text)