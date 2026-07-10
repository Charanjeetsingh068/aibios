import base64
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


class GoogleVoiceProvider(VoiceProvider):
    name = "google_tts"

    async def list_voices(self, api_key: str, region: Optional[str] = None) -> List[VoiceInfo]:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            res = await client.get("https://texttospeech.googleapis.com/v1/voices", params={"key": api_key})
        if res.status_code != 200:
            raise VoiceProviderAPIError(res.text, status_code=res.status_code)
        voices = res.json().get("voices", [])
        return [
            VoiceInfo(
                provider_voice_id=v.get("name"),
                name=v.get("name"),
                language=(v.get("languageCodes") or [None])[0],
                gender=v.get("ssmlGender"),
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
        # Google voice names encode their locale, e.g. "en-US-Neural2-C" — the API requires
        # languageCode to match the voice's own locale.
        parts = voice_id.split("-")
        language_code = "-".join(parts[:2]) if len(parts) >= 2 else "en-US"
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            res = await client.post(
                "https://texttospeech.googleapis.com/v1/text:synthesize",
                params={"key": api_key},
                json={
                    "input": {"text": text},
                    "voice": {"languageCode": language_code, "name": voice_id},
                    "audioConfig": {"audioEncoding": "MP3"},
                },
            )
        if res.status_code != 200:
            raise VoiceProviderAPIError(res.text, status_code=res.status_code)
        audio_content_b64 = res.json().get("audioContent", "")
        return base64.b64decode(audio_content_b64)
