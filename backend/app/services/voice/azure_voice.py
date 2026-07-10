from typing import List, Optional
from xml.sax.saxutils import escape

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.services.voice.base import (
    VoiceInfo,
    VoiceProvider,
    VoiceProviderAPIError,
    VoiceProviderNotConfiguredError,
)

REQUEST_TIMEOUT_SECONDS = 30.0
RETRYABLE_EXCEPTIONS = (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout)


class AzureVoiceProvider(VoiceProvider):
    name = "azure_speech"

    async def list_voices(self, api_key: str, region: Optional[str] = None) -> List[VoiceInfo]:
        if not region:
            raise VoiceProviderNotConfiguredError("Azure Speech requires a region (AZURE_SPEECH_REGION).")
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            res = await client.get(
                f"https://{region}.tts.speech.microsoft.com/cognitiveservices/voices/list",
                headers={"Ocp-Apim-Subscription-Key": api_key},
            )
        if res.status_code != 200:
            raise VoiceProviderAPIError(res.text, status_code=res.status_code)
        voices = res.json()
        return [
            VoiceInfo(
                provider_voice_id=v.get("ShortName"),
                name=v.get("DisplayName", v.get("ShortName")),
                language=v.get("Locale"),
                gender=v.get("Gender"),
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
        if not region:
            raise VoiceProviderNotConfiguredError("Azure Speech requires a region (AZURE_SPEECH_REGION).")
        locale = voice_id.split("-")[0] + "-" + voice_id.split("-")[1] if voice_id.count("-") >= 2 else "en-US"
        ssml = (
            f'<speak version="1.0" xml:lang="{locale}">'
            f'<voice name="{escape(voice_id)}">{escape(text)}</voice></speak>'
        )
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            res = await client.post(
                f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1",
                headers={
                    "Ocp-Apim-Subscription-Key": api_key,
                    "Content-Type": "application/ssml+xml",
                    "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3",
                },
                content=ssml.encode("utf-8"),
            )
        if res.status_code != 200:
            raise VoiceProviderAPIError(res.text, status_code=res.status_code)
        return res.content
