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
CARTESIA_VERSION = "2024-06-10"


class CartesiaVoiceProvider(VoiceProvider):
    name = "cartesia"

    async def list_voices(self, api_key: str, region: Optional[str] = None) -> List[VoiceInfo]:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            res = await client.get(
                "https://api.cartesia.ai/voices",
                headers={"X-API-Key": api_key, "Cartesia-Version": CARTESIA_VERSION},
            )
        if res.status_code != 200:
            raise VoiceProviderAPIError(res.text, status_code=res.status_code)
        voices = res.json()
        if isinstance(voices, dict):
            voices = voices.get("data", [])
        return [
            VoiceInfo(
                provider_voice_id=v.get("id"),
                name=v.get("name", v.get("id")),
                language=v.get("language"),
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
                "https://api.cartesia.ai/tts/bytes",
                headers={"X-API-Key": api_key, "Cartesia-Version": CARTESIA_VERSION, "Content-Type": "application/json"},
                json={
                    "model_id": "sonic-english",
                    "transcript": text,
                    "voice": {"mode": "id", "id": voice_id},
                    "output_format": {"container": "mp3", "sample_rate": 44100, "encoding": "mp3"},
                },
            )
        if res.status_code != 200:
            raise VoiceProviderAPIError(res.text, status_code=res.status_code)
        return res.content
