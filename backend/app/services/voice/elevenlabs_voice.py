from typing import List, Optional

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.services.voice.base import VoiceInfo, VoiceProvider, VoiceProviderAPIError

REQUEST_TIMEOUT_SECONDS = 30.0
RETRYABLE_EXCEPTIONS = (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout)


class ElevenLabsVoiceProvider(VoiceProvider):
    name = "elevenlabs"

    async def list_voices(self, api_key: str, region: Optional[str] = None) -> List[VoiceInfo]:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            res = await client.get("https://api.elevenlabs.io/v1/voices", headers={"xi-api-key": api_key})
        if res.status_code != 200:
            raise VoiceProviderAPIError(res.text, status_code=res.status_code)
        voices = res.json().get("voices", [])
        return [
            VoiceInfo(
                provider_voice_id=v.get("voice_id"),
                name=v.get("name", v.get("voice_id")),
                language=(v.get("labels") or {}).get("language"),
                gender=(v.get("labels") or {}).get("gender"),
                preview_url=v.get("preview_url"),
            )
            for v in voices
        ]

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
    )
    async def synthesize(self, api_key: str, text: str, voice_id: str, region: Optional[str] = None) -> bytes:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            res = await client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                headers={"xi-api-key": api_key, "Content-Type": "application/json"},
                json={"text": text, "model_id": "eleven_monolingual_v1"},
            )
        if res.status_code != 200:
            raise VoiceProviderAPIError(res.text, status_code=res.status_code)
        return res.content
