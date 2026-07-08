from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


class VoiceProviderNotConfiguredError(Exception):
    """Raised when a provider's API key isn't available (neither a per-organization
    VoiceProviderCredential row nor the matching global settings.<PROVIDER>_API_KEY)."""


class VoiceProviderAPIError(Exception):
    """Raised when the provider's real API itself returns an error — distinct from
    NotConfigured, so callers can report an honest upstream failure."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


@dataclass
class VoiceInfo:
    provider_voice_id: str
    name: str
    language: Optional[str] = None
    gender: Optional[str] = None
    preview_url: Optional[str] = None


class VoiceProvider(ABC):
    """Common contract every AI voice provider module implements. Credential resolution
    (org override vs. global settings fallback) happens in registry.py — implementations
    here just take the resolved api_key/region as plain arguments, matching the functional
    style of meta_service.py / whatsapp_service.py rather than hiding config lookups inside
    the provider itself."""

    name: str

    @abstractmethod
    async def list_voices(self, api_key: str, region: Optional[str] = None) -> List[VoiceInfo]:
        ...

    @abstractmethod
    async def synthesize(self, api_key: str, text: str, voice_id: str, region: Optional[str] = None) -> bytes:
        """Returns real synthesized audio bytes for the given text/voice."""
        ...
