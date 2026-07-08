import logging
from datetime import datetime
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.auth import User
from app.models.integrations import Integration

logger = logging.getLogger(__name__)
router = APIRouter()

# Each channel's required backend credentials. A channel can only ever move
# past "not_configured" once every one of these settings has a real value.
CHANNEL_REQUIREMENTS: Dict[str, List[str]] = {
    "facebook": ["FACEBOOK_APP_ID", "FACEBOOK_APP_SECRET", "FACEBOOK_REDIRECT_URI"],
    "instagram": ["FACEBOOK_APP_ID", "FACEBOOK_APP_SECRET", "FACEBOOK_REDIRECT_URI"],
    "whatsapp": ["WHATSAPP_APP_ID", "WHATSAPP_APP_SECRET", "WHATSAPP_ACCESS_TOKEN", "WHATSAPP_PHONE_NUMBER_ID"],
    "google_sheets": ["GOOGLE_SERVICE_ACCOUNT_JSON"],
    "ai_voice": [],  # satisfied if ANY provider below is configured
}

AI_VOICE_PROVIDERS: Dict[str, List[str]] = {
    "openai_realtime": ["OPENAI_API_KEY"],
    "twilio": ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE_NUMBER"],
    "elevenlabs": ["ELEVENLABS_API_KEY"],
}


def _missing_settings(channel: str) -> List[str]:
    if channel == "ai_voice":
        for provider_keys in AI_VOICE_PROVIDERS.values():
            if all(getattr(settings, key, None) for key in provider_keys):
                return []
        return [f"one provider fully configured: {AI_VOICE_PROVIDERS}"]
    required = CHANNEL_REQUIREMENTS.get(channel)
    if required is None:
        raise HTTPException(status_code=404, detail=f"Unknown integration channel '{channel}'")
    return [key for key in required if not getattr(settings, key, None)]


async def _get_or_create(db: AsyncSession, organization_id: str, channel: str) -> Integration:
    result = await db.execute(
        select(Integration).where(Integration.organization_id == organization_id, Integration.channel == channel)
    )
    row = result.scalar_one_or_none()
    if not row:
        row = Integration(organization_id=organization_id, channel=channel, status="not_connected")
        db.add(row)
        await db.commit()
        await db.refresh(row)
    return row


def _serialize(row: Integration, missing: List[str]) -> Dict[str, Any]:
    effective_status = "not_configured" if missing else row.status
    return {
        "id": row.id,
        "channel": row.channel,
        "status": effective_status,
        "external_account_id": row.external_account_id,
        "detail": row.detail,
        "missing_configuration": missing,
        "connected_at": row.connected_at.isoformat() if row.connected_at else None,
    }


@router.get("", response_model=Dict[str, Any])
async def list_integrations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    channels = list(CHANNEL_REQUIREMENTS.keys())
    items = []
    for channel in channels:
        row = await _get_or_create(db, current_user.organization_id, channel)
        items.append(_serialize(row, _missing_settings(channel)))
    return {"integrations": items}


@router.post("/{channel}/connect", response_model=Dict[str, Any])
async def connect_integration(
    channel: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    missing = _missing_settings(channel)
    row = await _get_or_create(db, current_user.organization_id, channel)

    if missing:
        row.status = "not_connected"
        row.detail = f"Cannot connect: missing backend configuration {missing}"
        await db.commit()
        raise HTTPException(
            status_code=501,
            detail=(
                f"{channel} integration is not configured on this server. "
                f"Set the following environment variables and restart the backend: {missing}"
            ),
        )

    # Credentials exist — a real OAuth/connect flow would begin here for the
    # given channel. None have been implemented yet because no channel has
    # its full credential set configured in this environment.
    raise HTTPException(
        status_code=501,
        detail=f"{channel} credentials are configured but the OAuth connect flow is not yet implemented.",
    )


@router.post("/{channel}/disconnect", response_model=Dict[str, Any])
async def disconnect_integration(
    channel: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = await _get_or_create(db, current_user.organization_id, channel)
    row.status = "not_connected"
    row.external_account_id = None
    row.connected_at = None
    row.detail = "Disconnected by user"
    await db.commit()
    return _serialize(row, _missing_settings(channel))
