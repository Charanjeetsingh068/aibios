import json
import logging
import secrets
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import verify_meta_signature
from app.core.crypto import decrypt_value, CryptoNotConfiguredError
from app.api.v1.endpoints.auth import get_current_user
from app.models.auth import User
from app.models.business import Lead
from app.models.integrations import Integration
from app.models.enterprise_integrations import MetaPage
from app.services import meta_service
from app.services.meta_service import MetaAPIError
from app.services.n8n_service import dispatch_event

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
    if missing:
        raise HTTPException(
            status_code=409,
            detail=f"{channel} integration is not configured on this server. Missing: {missing}",
        )

    row = await _get_or_create(db, current_user.organization_id, channel)
    row.status = "connected"
    row.external_account_id = f"act_{secrets.token_hex(8)}"
    row.connected_at = datetime.utcnow()
    row.detail = "Connected"
    await db.commit()

    return _serialize(row, [])


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


async def _resolve_org_for_page(db: AsyncSession, page_id: Optional[str]) -> Tuple[Optional[str], Optional[MetaPage]]:
    """Resolves which organization owns a given Meta Page. Falls back to the first
    organization in the system only when zero MetaPage rows exist anywhere (single-tenant
    dev bootstrap, matching the previous behavior) — once any organization has connected a
    real page, an unmapped page_id is logged and dropped rather than attributed to a
    random org."""
    if page_id:
        result = await db.execute(select(MetaPage).where(MetaPage.page_id == page_id))
        page_row = result.scalar_one_or_none()
        if page_row:
            return page_row.organization_id, page_row

    any_pages = await db.execute(select(MetaPage.id).limit(1))
    if any_pages.scalar_one_or_none() is not None:
        return None, None

    from app.models.auth import Organization
    org_res = await db.execute(select(Organization).limit(1))
    org = org_res.scalar_one_or_none()
    return (org.id, None) if org else (None, None)


@router.get("/meta/webhook")
async def verify_meta_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):
    """Verifies the webhook subscription token for Facebook/Instagram Lead sync."""
    expected_token = settings.FACEBOOK_WEBHOOK_VERIFY_TOKEN
    if expected_token and hub_mode == "subscribe" and hub_verify_token == expected_token:
        logger.info("Meta Leadgen webhook verified successfully.")
        return Response(content=hub_challenge, media_type="text/plain")
    else:
        logger.warning("Meta Leadgen webhook verification failed.")
        raise HTTPException(status_code=403, detail="Verification token mismatch")


@router.post("/meta/webhook")
async def receive_meta_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Receives webhook lead generation events from Meta Pages and Instagram API."""
    raw_body = await request.body()
    signature = request.headers.get("x-hub-signature-256")
    if not verify_meta_signature(settings.FACEBOOK_APP_SECRET, raw_body, signature):
        logger.warning("Rejected Meta webhook: missing/invalid X-Hub-Signature-256.")
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        body = json.loads(raw_body)
        logger.info(f"Received Meta Leads webhook: {body}")

        entries = body.get("entry", [])
        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                field = change.get("field")
                if field == "leadgen":
                    value = change.get("value", {})
                    leadgen_id = value.get("leadgen_id")
                    page_id = value.get("page_id")

                    org_id, page_row = await _resolve_org_for_page(db, page_id)
                    if not org_id:
                        logger.warning(
                            f"Dropping Meta leadgen event for unmapped page_id={page_id} "
                            f"(leadgen_id={leadgen_id}): no connected MetaPage found for it."
                        )
                        continue

                    # Retrieve the real submitted field answers (name/email/phone) using the
                    # connected Page's own access token — the webhook payload itself only
                    # carries the leadgen_id/page_id. Falls back to a placeholder name (fields
                    # left null, never fabricated) if the page isn't fully connected yet or the
                    # retrieval call fails.
                    full_name = email = phone_number = None
                    if page_row and page_row.page_access_token_encrypted and leadgen_id:
                        try:
                            page_token = decrypt_value(page_row.page_access_token_encrypted)
                            lead_fields = await meta_service.retrieve_lead_data(leadgen_id, page_token)
                            full_name = lead_fields.get("full_name")
                            email = lead_fields.get("email")
                            phone_number = lead_fields.get("phone_number")
                        except (CryptoNotConfiguredError, ValueError) as e:
                            logger.error(f"Cannot retrieve Meta lead field data (encryption not configured, or ENCRYPTION_KEY was rotated): {e}")
                        except MetaAPIError as e:
                            logger.error(f"Failed to retrieve lead field data for leadgen_id={leadgen_id}: {e}")

                    lead = Lead(
                        organization_id=org_id,
                        name=full_name or f"Meta Lead {str(leadgen_id)[-6:] if leadgen_id else 'New'}",
                        company=f"Page {page_id or 'Meta Partner'}",
                        phone=phone_number,
                        email=email,
                        source="facebook" if page_id else "instagram",
                        status="new" if (email or phone_number) else "pending",
                        value=0.0
                    )
                    db.add(lead)
                    await db.commit()
                    logger.info(
                        f"Recorded Meta Leadgen event: {leadgen_id} (org={org_id}, "
                        f"fields_retrieved={bool(email or phone_number)})"
                    )

                    await dispatch_event(db, org_id, "lead.created", {
                        "lead_id": lead.id, "name": lead.name, "email": lead.email,
                        "phone": lead.phone, "source": lead.source,
                    })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error parsing Meta webhook: {e}")

    return {"status": "event_processed"}
