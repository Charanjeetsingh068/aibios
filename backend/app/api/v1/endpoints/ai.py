import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.config import settings
from app.api.v1.endpoints.auth import get_current_user
from app.models.auth import User
from app.services.openai_service import get_chat_stream, OpenAINotConfiguredError

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatMessage(BaseModel):
    role: str  # "system" | "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]


@router.post("/chat")
async def chat(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    """Streams a real OpenAI chat completion. The caller sends the full conversation
    history each time (messages carries prior turns) so context is preserved across
    calls — this endpoint itself is stateless, matching the OpenAI API's own design."""
    if not body.messages:
        raise HTTPException(status_code=400, detail="messages must not be empty")
    if not settings.OPENAI_API_KEY:
        # Fail before the stream starts (and headers are sent) so this is a real 503,
        # not a 200 with an error message hidden in the body.
        raise HTTPException(status_code=503, detail="OpenAI is not configured on this server (missing OPENAI_API_KEY).")

    async def event_stream():
        try:
            async for chunk in get_chat_stream([m.model_dump() for m in body.messages]):
                yield chunk
        except OpenAINotConfiguredError:
            # Key could still be revoked/removed between the check above and the first
            # chunk; report it the same way as any other mid-stream failure.
            logger.warning("OpenAI became unavailable mid-request.")
            yield "\n[error: OpenAI is not configured on this server]"
        except Exception as e:
            logger.error(f"OpenAI chat stream failed after retries: {e}")
            yield "\n[error: AI service temporarily unavailable]"

    return StreamingResponse(event_stream(), media_type="text/plain")
