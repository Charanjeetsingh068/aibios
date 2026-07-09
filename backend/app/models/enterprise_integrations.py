from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.auth import Base, generate_uuid


class IntegrationCredential(Base):
    """Generic per-organization OAuth credential store, one row per (organization, provider).
    Tokens are stored encrypted (see app/core/crypto.py) — never plaintext."""
    __tablename__ = "integration_credentials"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[str] = mapped_column(String(30), nullable=False)  # meta, n8n
    access_token_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    refresh_token_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    token_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    scope: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    external_user_id: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="connected")  # connected, expired, error
    last_error: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    last_refreshed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MetaPage(Base):
    """A connected Facebook Page (and optionally its linked Instagram Business account)
    for an organization. Multiple rows per org = multi-page support."""
    __tablename__ = "meta_pages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    credential_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("integration_credentials.id", ondelete="SET NULL"), nullable=True)
    page_id: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    page_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    page_access_token_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    instagram_business_account_id: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    instagram_username: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    webhook_subscribed: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(20), default="connected")  # connected, error, disconnected
    last_error: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    connected_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MetaLeadForm(Base):
    """A Meta Lead Ads form discovered for a connected Page."""
    __tablename__ = "meta_lead_forms"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    meta_page_id: Mapped[str] = mapped_column(String(36), ForeignKey("meta_pages.id", ondelete="CASCADE"), nullable=False)
    form_id: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    form_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)  # ACTIVE, ARCHIVED (as reported by Meta)
    discovered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class WhatsAppPhoneNumber(Base):
    """A registered WhatsApp Business phone number for an organization. Multiple rows per
    org = multi-number support. access_token_encrypted is an optional per-org override;
    when null, callers fall back to the global settings.WHATSAPP_ACCESS_TOKEN."""
    __tablename__ = "whatsapp_phone_numbers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    phone_number_id: Mapped[str] = mapped_column(String(60), nullable=False, index=True, unique=True)
    display_phone_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    waba_id: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    access_token_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    verified_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    quality_rating: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="connected")  # connected, error, disconnected
    last_error: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    registered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WhatsAppMessageLog(Base):
    """Log of every inbound/outbound WhatsApp message, including delivery/read status."""
    __tablename__ = "whatsapp_message_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    phone_number_row_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("whatsapp_phone_numbers.id", ondelete="SET NULL"), nullable=True)
    wa_message_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)  # inbound, outbound
    to_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    from_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    message_type: Mapped[str] = mapped_column(String(20), default="text")  # text, image, video, document, audio, template
    template_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    media_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="queued")  # queued, sent, delivered, read, failed
    status_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    lead_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("leads.id", ondelete="SET NULL"), nullable=True)
    raw_payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class VoiceProviderCredential(Base):
    """Per-organization API key override for an AI voice provider. When absent, providers
    fall back to the matching global settings.<PROVIDER>_API_KEY."""
    __tablename__ = "voice_provider_credentials"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[str] = mapped_column(String(30), nullable=False)  # openai_realtime, elevenlabs, cartesia, azure_speech, google_tts
    api_key_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    region: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # azure_speech only
    status: Mapped[str] = mapped_column(String(20), default="connected")
    last_error: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class VoiceLibraryEntry(Base):
    """A voice available to an organization — either synced from a provider's voice catalog,
    or a locally-uploaded reference audio file."""
    __tablename__ = "voice_library_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)  # null when source == "upload"
    provider_voice_id: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    source: Mapped[str] = mapped_column(String(20), default="provider")  # provider, upload
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # upload only
    preview_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CampaignVoiceAssignment(Base):
    """Which voice a campaign uses for outbound AI voice calls. One active assignment per
    campaign — re-assigning updates the existing row rather than appending."""
    __tablename__ = "campaign_voice_assignments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    campaign_id: Mapped[str] = mapped_column(String(36), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, unique=True)
    voice_id: Mapped[str] = mapped_column(String(36), ForeignKey("voice_library_entries.id", ondelete="CASCADE"), nullable=False)
    assigned_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


