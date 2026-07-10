import logging
from typing import AsyncGenerator, Dict, List

from openai import APIConnectionError, APITimeoutError, AsyncOpenAI, RateLimitError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings

logger = logging.getLogger(__name__)

# Transient failure classes worth retrying; auth/invalid-request errors are not retried
# since retrying them can never succeed.
RETRYABLE_EXCEPTIONS = (APIConnectionError, APITimeoutError, RateLimitError)

REQUEST_TIMEOUT_SECONDS = 30.0


class OpenAINotConfiguredError(Exception):
    """Raised when OPENAI_API_KEY isn't set — distinct from a real API failure so callers
    can report an honest 'not configured' status instead of a generic error."""


def get_openai_client() -> AsyncOpenAI:
    if not settings.OPENAI_API_KEY:
        raise OpenAINotConfiguredError("OPENAI_API_KEY is not set.")
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY, timeout=REQUEST_TIMEOUT_SECONDS)


@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
)
async def _create_chat_completion_stream(client: AsyncOpenAI, messages: List[Dict[str, str]], model: str):
    """Opens the streaming completion request, retrying transient connection/timeout/
    rate-limit failures with exponential backoff before any content has been yielded."""
    return await client.chat.completions.create(model=model, messages=messages, stream=True)


async def get_chat_stream(messages: List[Dict[str, str]], model: str = "gpt-4o") -> AsyncGenerator[str, None]:
    """Streams response chunks from OpenAI's Chat Completions endpoint. `messages` carries
    the full conversation history (system/user/assistant turns) so context is preserved
    across turns — the caller is responsible for accumulating and passing prior turns back
    in on each call, matching the OpenAI Chat Completions API's stateless design.

    Raises OpenAINotConfiguredError if no API key is set, or the underlying OpenAI
    exception after retries are exhausted — callers should catch and surface a real error
    rather than receiving a fabricated response, per the no-fake-data policy."""
    client = get_openai_client()
    response = await _create_chat_completion_stream(client, messages, model)
    async for chunk in response:
        content = chunk.choices[0].delta.content
        if content is not None:
            yield content


# Production tool schemas for OpenAI function calling
CRM_FUNCTIONS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "create_crm_lead",
            "description": "Registers a new business lead in the CRM",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Lead user full name"},
                    "company": {"type": "string", "description": "Organization company name"},
                    "phone": {"type": "string", "description": "Contact telephone number"},
                    "email": {"type": "string", "description": "Email address identifier"},
                    "value": {"type": "number", "description": "Estimated pipeline value of this deal"}
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "schedule_crm_meeting",
            "description": "Logs and schedules a calendar meeting task",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Meeting subject title"},
                    "scheduled_at": {"type": "string", "description": "ISO-8601 calendar date time"}
                },
                "required": ["title", "scheduled_at"]
            }
        }
    }
]
