from typing import Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.crypto import decrypt_value, CryptoNotConfiguredError
from app.models.enterprise_integrations import VoiceProviderCredential
from app.services.voice.base import VoiceProvider, VoiceInfo, VoiceProviderNotConfiguredError
from app.services.voice.openai_voice import OpenAIVoiceProvider
from app.services.voice.elevenlabs_voice import ElevenLabsVoiceProvider
from app.services.voice.cartesia_voice import CartesiaVoiceProvider
from app.services.voice.azure_voice import AzureVoiceProvider
from app.services.voice.google_voice import GoogleVoiceProvider

PROVIDERS: Dict[str, VoiceProvider] = {
    "openai_realtime": OpenAIVoiceProvider(),
    "elevenlabs": ElevenLabsVoiceProvider(),
    "cartesia": CartesiaVoiceProvider(),
    "azure_speech": AzureVoiceProvider(),
    "google_tts": GoogleVoiceProvider(),
}

# Maps provider name to its global settings.<KEY> fallback field name(s).
_GLOBAL_API_KEY_FIELD: Dict[str, str] = {
    "openai_realtime": "OPENAI_API_KEY",
    "elevenlabs": "ELEVENLABS_API_KEY",
    "cartesia": "CARTESIA_API_KEY",
    "azure_speech": "AZURE_SPEECH_KEY",
    "google_tts": "GOOGLE_TTS_API_KEY",
}
_GLOBAL_REGION_FIELD: Dict[str, str] = {
    "azure_speech": "AZURE_SPEECH_REGION",
}


def get_provider(provider_name: str) -> VoiceProvider:
    provider = PROVIDERS.get(provider_name)
    if not provider:
        raise ValueError(f"Unknown voice provider '{provider_name}'. Valid providers: {list(PROVIDERS.keys())}")
    return provider


async def resolve_credential(db: AsyncSession, organization_id: str, provider_name: str) -> Tuple[str, Optional[str]]:
    """Resolves (api_key, region) for a provider: prefers a per-organization
    VoiceProviderCredential row, falling back to the matching global settings.<PROVIDER>_API_KEY.
    Raises VoiceProviderNotConfiguredError if neither is available."""
    if provider_name not in PROVIDERS:
        raise ValueError(f"Unknown voice provider '{provider_name}'.")

    result = await db.execute(
        select(VoiceProviderCredential).where(
            VoiceProviderCredential.organization_id == organization_id,
            VoiceProviderCredential.provider == provider_name,
            VoiceProviderCredential.status == "connected",
        )
    )
    row = result.scalar_one_or_none()
    if row and row.api_key_encrypted:
        api_key = decrypt_value(row.api_key_encrypted)  # CryptoNotConfiguredError bubbles up intentionally
        return api_key, row.region

    global_key = getattr(settings, _GLOBAL_API_KEY_FIELD[provider_name], None)
    global_region_field = _GLOBAL_REGION_FIELD.get(provider_name)
    global_region = getattr(settings, global_region_field, None) if global_region_field else None
    if global_key:
        return global_key, global_region

    raise VoiceProviderNotConfiguredError(
        f"Voice provider '{provider_name}' is not configured for this organization "
        f"(no stored credential, and no {_GLOBAL_API_KEY_FIELD[provider_name]} fallback set)."
    )


async def list_voices_for_org(db: AsyncSession, organization_id: str, provider_name: str) -> List[VoiceInfo]:
    api_key, region = await resolve_credential(db, organization_id, provider_name)
    provider = get_provider(provider_name)
    return await provider.list_voices(api_key, region=region)


async def synthesize_for_org(db: AsyncSession, organization_id: str, provider_name: str, text: str, voice_id: str) -> bytes:
    api_key, region = await resolve_credential(db, organization_id, provider_name)
    provider = get_provider(provider_name)
    return await provider.synthesize(api_key, text, voice_id, region=region)


async def is_provider_configured(db: AsyncSession, organization_id: str, provider_name: str) -> bool:
    try:
        await resolve_credential(db, organization_id, provider_name)
        return True
    except (VoiceProviderNotConfiguredError, CryptoNotConfiguredError):
        return False
