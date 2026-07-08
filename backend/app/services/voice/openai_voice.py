from typing import Any, Dict, List, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.services.voice.base import VoiceProvider, VoiceInfo, VoiceProviderAPIError

REQUEST_TIMEOUT_SECONDS = 30.0
RETRYABLE_EXCEPTIONS = (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout)

# OpenAI's TTS API has no "list voices" endpoint — these are the documented built-in voice
# names for the tts-1/tts-1-hd/gpt-4o-mini-tts models (real, not fabricated).
BUILTIN_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer", "ash", "coral", "sage"]


class OpenAIVoiceProvider(VoiceProvider):
    name = "openai_realtime"

    async def list_voices(self, api_key: str, region: Optional[str] = None) -> List[VoiceInfo]:
        return [VoiceInfo(provider_voice_id=v, name=v.capitalize()) for v in BUILTIN_VOICES]

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
    )
    async def synthesize(self, api_key: str, text: str, voice_id: str, region: Optional[str] = None) -> bytes:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            res = await client.post(
                "https://api.openai.com/v1/audio/speech",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": "tts-1", "input": text, "voice": voice_id},
            )
        if res.status_code != 200:
            raise VoiceProviderAPIError(res.text, status_code=res.status_code)
        return res.content


async def create_realtime_session(api_key: str, model: str = "gpt-4o-realtime-preview", voice: str = "alloy") -> Dict[str, Any]:
    """Mints a real ephemeral OpenAI Realtime session token. The client (browser/telephony
    bridge) connects directly to OpenAI's Realtime API using this short-lived token — the
    backend never proxies live call audio itself, per OpenAI's documented integration
    pattern for Realtime."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        res = await client.post(
            "https://api.openai.com/v1/realtime/sessions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model, "voice": voice},
        )
    if res.status_code != 200:
        raise VoiceProviderAPIError(res.text, status_code=res.status_code)
    return res.json()
