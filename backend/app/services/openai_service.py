import json
import logging
from typing import Any, AsyncGenerator, Dict, List
from openai import AsyncOpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_openai_client() -> AsyncOpenAI:
    """Returns an instance of AsyncOpenAI client."""
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY or "dummy_openai_api_key_placeholder")


async def get_chat_stream(messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
    """Streams response chunks from OpenAI's Chat Completions endpoint."""
    client = get_openai_client()
    try:
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            stream=True
        )
        async for chunk in response:
            content = chunk.choices[0].delta.content
            if content is not None:
                yield content
    except Exception as e:
        logger.error(f"OpenAI chat stream call failed: {e}")
        fallback_msg = "This is a simulated AI agent stream response. Connect your OpenAI API Key to stream real GPT-4 answers."
        for word in fallback_msg.split(" "):
            yield word + " "
            import asyncio
            await asyncio.sleep(0.03)


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
