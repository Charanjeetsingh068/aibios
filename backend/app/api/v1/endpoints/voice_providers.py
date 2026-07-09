import os
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile
from fastapi.responses import Response as RawResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.crypto import encrypt_value, CryptoNotConfiguredError
from app.api.v1.endpoints.auth import get_current_user, PermissionChecker
from app.models.auth import User
from app.models.business import Campaign
from app.models.enterprise_integrations import VoiceProviderCredential, VoiceLibraryEntry, CampaignVoiceAssignment
from app.services.voice.registry import PROVIDERS, is_provider_configured, list_voices_for_org, synthesize_for_org, resolve_credential
from app.services.voice.base import VoiceProviderNotConfiguredError, VoiceProviderAPIError
from app.services.voice.openai_voice import create_realtime_session

logger = logging.getLogger(__name__)
router = APIRouter()

require_voice_write = PermissionChecker("voice.admin")
require_voice_read = PermissionChecker("voice.read")

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
MAX_VOICE_UPLOAD_BYTES = 25 * 1024 * 1024
DEFAULT_PREVIEW_TEXT = "Hello, this is a preview of this voice."


class StoreCredentialBody(BaseModel):
    api_key: str
    region: Optional[str] = None  # azure_speech only


class SyncLibraryEntry(BaseModel):
    provider_voice_id: str
    name: str
    language: Optional[str] = None
    gender: Optional[str] = None
    preview_url: Optional[str] = None


class PreviewBody(BaseModel):
    text: Optional[str] = None


class RealtimeSessionBody(BaseModel):
    voice: str = "alloy"
    model: str = "gpt-4o-realtime-preview"


class AssignVoiceBody(BaseModel):
    voice_id: str


def _serialize_library_entry(entry: VoiceLibraryEntry) -> Dict[str, Any]:
    return {
        "id": entry.id,
        "provider": entry.provider,
        "provider_voice_id": entry.provider_voice_id,
        "name": entry.name,
        "description": entry.description,
        "language": entry.language,
        "gender": entry.gender,
        "source": entry.source,
        "preview_url": entry.preview_url,
        "status": entry.status,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
    }


@router.get("/providers", response_model=Dict[str, Any])
async def list_providers(
    current_user: User = Depends(require_voice_read),
    db: AsyncSession = Depends(get_db),
):
    """Reports configured/not_configured status per AI voice provider for this
    organization (org-level credential, or the global settings fallback)."""
    statuses = {}
    for name in PROVIDERS:
        configured = await is_provider_configured(db, current_user.organization_id, name)
        statuses[name] = {"status": "configured" if configured else "not_configured"}
    return {"providers": statuses}


@router.post("/providers/{name}/credentials", response_model=Dict[str, Any])
async def store_provider_credentials(
    name: str,
    body: StoreCredentialBody,
    current_user: User = Depends(require_voice_write),
    db: AsyncSession = Depends(get_db),
):
    """Stores an org-level API key override (encrypted) for a voice provider."""
    if name not in PROVIDERS:
        raise HTTPException(status_code=404, detail=f"Unknown voice provider '{name}'.")

    try:
        encrypted_key = encrypt_value(body.api_key)
    except (CryptoNotConfiguredError, ValueError):
        raise HTTPException(status_code=503, detail="Stored credential could not be decrypted (encryption not configured, or ENCRYPTION_KEY was rotated).")

    result = await db.execute(
        select(VoiceProviderCredential).where(
            VoiceProviderCredential.organization_id == current_user.organization_id,
            VoiceProviderCredential.provider == name,
        )
    )
    row = result.scalar_one_or_none()
    if not row:
        row = VoiceProviderCredential(organization_id=current_user.organization_id, provider=name)
        db.add(row)

    row.api_key_encrypted = encrypted_key
    row.region = body.region
    row.status = "connected"
    row.last_error = None
    await db.commit()
    return {"provider": name, "status": "connected"}


@router.get("/library", response_model=Dict[str, Any])
async def list_library(
    current_user: User = Depends(require_voice_read),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(VoiceLibraryEntry).where(VoiceLibraryEntry.organization_id == current_user.organization_id)
    )
    entries = result.scalars().all()
    return {"voices": [_serialize_library_entry(e) for e in entries]}


@router.post("/library/sync/{provider}", response_model=Dict[str, Any])
async def sync_library(
    provider: str,
    current_user: User = Depends(require_voice_write),
    db: AsyncSession = Depends(get_db),
):
    """Fetches the real voice catalog from a configured provider and upserts it into the
    organization's voice library."""
    if provider not in PROVIDERS:
        raise HTTPException(status_code=404, detail=f"Unknown voice provider '{provider}'.")

    try:
        voices = await list_voices_for_org(db, current_user.organization_id, provider)
    except VoiceProviderNotConfiguredError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except (CryptoNotConfiguredError, ValueError):
        raise HTTPException(status_code=503, detail="Stored credential could not be decrypted (encryption not configured, or ENCRYPTION_KEY was rotated).")
    except VoiceProviderAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))

    for v in voices:
        result = await db.execute(
            select(VoiceLibraryEntry).where(
                VoiceLibraryEntry.organization_id == current_user.organization_id,
                VoiceLibraryEntry.provider == provider,
                VoiceLibraryEntry.provider_voice_id == v.provider_voice_id,
            )
        )
        entry = result.scalar_one_or_none()
        if not entry:
            entry = VoiceLibraryEntry(
                organization_id=current_user.organization_id,
                provider=provider,
                provider_voice_id=v.provider_voice_id,
                name=v.name,
                source="provider",
            )
            db.add(entry)
        entry.name = v.name
        entry.language = v.language
        entry.gender = v.gender
        entry.preview_url = v.preview_url
        entry.status = "active"
    await db.commit()

    result = await db.execute(
        select(VoiceLibraryEntry).where(
            VoiceLibraryEntry.organization_id == current_user.organization_id,
            VoiceLibraryEntry.provider == provider,
        )
    )
    return {"voices": [_serialize_library_entry(e) for e in result.scalars().all()]}


@router.post("/library/upload", response_model=Dict[str, Any])
async def upload_voice(
    file: UploadFile = FastAPIFile(...),
    name: Optional[str] = None,
    current_user: User = Depends(require_voice_write),
    db: AsyncSession = Depends(get_db),
):
    """Stores a locally-uploaded reference audio file as a voice library entry. This does
    NOT call any provider's voice-cloning API — it's stored as a reference asset only."""
    content = await file.read()
    if len(content) > MAX_VOICE_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"File exceeds maximum upload size of {MAX_VOICE_UPLOAD_BYTES // (1024*1024)} MB")

    entry = VoiceLibraryEntry(
        organization_id=current_user.organization_id,
        name=name or file.filename or "Uploaded Voice",
        source="upload",
        status="active",
    )
    db.add(entry)
    await db.flush()

    filepath = os.path.join(UPLOAD_DIR, f"voice_{entry.id}")
    with open(filepath, "wb") as f:
        f.write(content)
    entry.file_path = filepath

    await db.commit()
    return _serialize_library_entry(entry)


@router.post("/library/{voice_id}/preview")
async def preview_voice(
    voice_id: str,
    body: PreviewBody,
    current_user: User = Depends(require_voice_read),
    db: AsyncSession = Depends(get_db),
):
    """Synthesizes a real preview clip via the resolved provider for a provider-sourced
    voice. Uploaded (local) voices have no synthesis endpoint to call — this returns the
    stored file itself instead."""
    entry = await db.get(VoiceLibraryEntry, voice_id)
    if not entry or entry.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Voice not found.")

    if entry.source == "upload":
        if not entry.file_path or not os.path.exists(entry.file_path):
            raise HTTPException(status_code=404, detail="Uploaded voice file not found in storage.")
        with open(entry.file_path, "rb") as f:
            return RawResponse(content=f.read(), media_type="application/octet-stream")

    if not entry.provider or not entry.provider_voice_id:
        raise HTTPException(status_code=422, detail="This voice entry is missing provider details required for synthesis.")

    try:
        audio = await synthesize_for_org(db, current_user.organization_id, entry.provider, body.text or DEFAULT_PREVIEW_TEXT, entry.provider_voice_id)
        return RawResponse(content=audio, media_type="audio/mpeg")
    except VoiceProviderNotConfiguredError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except (CryptoNotConfiguredError, ValueError):
        raise HTTPException(status_code=503, detail="Stored credential could not be decrypted (encryption not configured, or ENCRYPTION_KEY was rotated).")
    except VoiceProviderAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/realtime-session", response_model=Dict[str, Any])
async def create_openai_realtime_session(
    body: RealtimeSessionBody,
    current_user: User = Depends(require_voice_write),
    db: AsyncSession = Depends(get_db),
):
    """Mints a real, short-lived OpenAI Realtime session for live AI voice calls. The
    client connects directly to OpenAI using the returned ephemeral token — this backend
    never proxies live call audio itself."""
    try:
        api_key, _region = await resolve_credential(db, current_user.organization_id, "openai_realtime")
        session = await create_realtime_session(api_key, model=body.model, voice=body.voice)
        return session
    except VoiceProviderNotConfiguredError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except (CryptoNotConfiguredError, ValueError):
        raise HTTPException(status_code=503, detail="Stored credential could not be decrypted (encryption not configured, or ENCRYPTION_KEY was rotated).")
    except VoiceProviderAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/campaigns/{campaign_id}/voice", response_model=Dict[str, Any])
async def assign_campaign_voice(
    campaign_id: str,
    body: AssignVoiceBody,
    current_user: User = Depends(require_voice_write),
    db: AsyncSession = Depends(get_db),
):
    campaign = await db.get(Campaign, campaign_id)
    if not campaign or campaign.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Campaign not found.")

    voice = await db.get(VoiceLibraryEntry, body.voice_id)
    if not voice or voice.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Voice not found.")

    result = await db.execute(select(CampaignVoiceAssignment).where(CampaignVoiceAssignment.campaign_id == campaign_id))
    assignment = result.scalar_one_or_none()
    if not assignment:
        assignment = CampaignVoiceAssignment(organization_id=current_user.organization_id, campaign_id=campaign_id, voice_id=body.voice_id)
        db.add(assignment)
    else:
        assignment.voice_id = body.voice_id
    assignment.assigned_by = current_user.id
    assignment.assigned_at = datetime.utcnow()
    await db.commit()

    return {"campaign_id": campaign_id, "voice_id": assignment.voice_id, "assigned_at": assignment.assigned_at.isoformat()}


@router.get("/campaigns/{campaign_id}/voice", response_model=Dict[str, Any])
async def get_campaign_voice(
    campaign_id: str,
    current_user: User = Depends(require_voice_read),
    db: AsyncSession = Depends(get_db),
):
    campaign = await db.get(Campaign, campaign_id)
    if not campaign or campaign.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Campaign not found.")

    result = await db.execute(select(CampaignVoiceAssignment).where(CampaignVoiceAssignment.campaign_id == campaign_id))
    assignment = result.scalar_one_or_none()
    if not assignment:
        return {"campaign_id": campaign_id, "voice_id": None}

    voice = await db.get(VoiceLibraryEntry, assignment.voice_id)
    return {
        "campaign_id": campaign_id,
        "voice_id": assignment.voice_id,
        "voice": _serialize_library_entry(voice) if voice else None,
        "assigned_at": assignment.assigned_at.isoformat() if assignment.assigned_at else None,
    }
