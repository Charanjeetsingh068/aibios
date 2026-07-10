import base64
import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import Response as RawResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import PermissionChecker, get_current_user
from app.core.config import settings
from app.core.crypto import CryptoNotConfiguredError, encrypt_value
from app.core.database import get_db
from app.core.security import verify_meta_signature
from app.models.auth import User
from app.models.business import Lead
from app.models.enterprise_integrations import WhatsAppMessageLog, WhatsAppPhoneNumber
from app.services import whatsapp_service
from app.services.event_bus import dispatch_event
from app.services.whatsapp_service import WhatsAppAPIError, WhatsAppNotConfiguredError

logger = logging.getLogger(__name__)
router = APIRouter()

require_whatsapp_write = PermissionChecker("whatsapp.admin")


class SendWAMessageBody(BaseModel):
    to_number: str
    message_text: str


class SendWATemplateBody(BaseModel):
    to_number: str
    template_name: str
    language_code: str = "en"


class SendWAMediaBody(BaseModel):
    to_number: str
    media_type: str  # image, video, document, audio
    link: Optional[str] = None
    media_id: Optional[str] = None
    caption: Optional[str] = None


class RegisterPhoneNumberBody(BaseModel):
    phone_number_id: str
    access_token: str
    pin: str


async def _resolve_org_for_phone_number_id(db: AsyncSession, phone_number_id: Optional[str]) -> Tuple[Optional[str], Optional[WhatsAppPhoneNumber]]:
    """Resolves which organization owns a given WhatsApp phone_number_id (from the webhook
    payload's value.metadata.phone_number_id). Falls back to the first organization only
    when zero WhatsAppPhoneNumber rows exist anywhere (single-tenant dev bootstrap using the
    global settings.WHATSAPP_PHONE_NUMBER_ID) — once any organization has registered a real
    number, an unmapped phone_number_id is logged and dropped rather than guessed."""
    if phone_number_id:
        result = await db.execute(select(WhatsAppPhoneNumber).where(WhatsAppPhoneNumber.phone_number_id == phone_number_id))
        row = result.scalar_one_or_none()
        if row:
            return row.organization_id, row

    any_rows = await db.execute(select(WhatsAppPhoneNumber.id).limit(1))
    if any_rows.scalar_one_or_none() is not None:
        return None, None

    from app.models.auth import Organization
    org_res = await db.execute(select(Organization).limit(1))
    org = org_res.scalar_one_or_none()
    return (org.id, None) if org else (None, None)


@router.get("/webhook")
async def verify_whatsapp_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):
    """Meta webhook verification endpoint."""
    expected_token = settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN
    if expected_token and hub_mode == "subscribe" and hub_verify_token == expected_token:
        logger.info("WhatsApp webhook verified successfully.")
        return Response(content=hub_challenge, media_type="text/plain")
    else:
        logger.warning("WhatsApp webhook verification failed.")
        raise HTTPException(status_code=403, detail="Verification token mismatch")


@router.post("/webhook")
async def receive_whatsapp_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Receives and parses incoming messages webhook events from Meta WhatsApp Cloud API."""
    raw_body = await request.body()
    signature = request.headers.get("x-hub-signature-256")
    if not verify_meta_signature(settings.WHATSAPP_APP_SECRET, raw_body, signature):
        logger.warning("Rejected WhatsApp webhook: missing/invalid X-Hub-Signature-256.")
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        body = json.loads(raw_body)
        logger.info(f"Received WhatsApp webhook body: {body}")

        entries = body.get("entry", [])
        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                phone_number_id = value.get("metadata", {}).get("phone_number_id")
                org_id, phone_row = await _resolve_org_for_phone_number_id(db, phone_number_id)
                if not org_id:
                    logger.warning(
                        f"Dropping WhatsApp webhook event for unmapped phone_number_id={phone_number_id}: "
                        "no connected WhatsAppPhoneNumber found for it."
                    )
                    continue

                # Incoming messages
                messages = value.get("messages", [])
                for msg in messages:
                    from_num = msg.get("from")
                    wa_message_id = msg.get("id")
                    msg_type = msg.get("type", "text")
                    text_obj = msg.get("text", {})
                    msg_text = text_obj.get("body", "")
                    contacts = value.get("contacts", [])
                    contact_name = contacts[0].get("profile", {}).get("name", "WhatsApp Lead") if contacts else "WhatsApp Lead"

                    lead_id = None
                    if from_num and msg_text:
                        lead = Lead(
                            organization_id=org_id,
                            name=contact_name,
                            phone=from_num,
                            source="whatsapp",
                            status="new",
                            value=0.0
                        )
                        db.add(lead)
                        await db.flush()
                        lead_id = lead.id
                        logger.info(f"Automatically created WhatsApp lead: {contact_name} ({from_num})")

                    log = WhatsAppMessageLog(
                        organization_id=org_id,
                        phone_number_row_id=phone_row.id if phone_row else None,
                        wa_message_id=wa_message_id,
                        direction="inbound",
                        from_number=from_num,
                        message_type=msg_type,
                        status="received",
                        status_updated_at=datetime.utcnow(),
                        lead_id=lead_id,
                        raw_payload=json.dumps(msg),
                    )
                    db.add(log)
                    await db.flush()

                    await dispatch_event(db, org_id, "whatsapp.message.received", {
                        "wa_message_id": wa_message_id, "from": from_num, "text": msg_text,
                        "message_type": msg_type, "lead_id": lead_id,
                    })

                # Delivery/read status updates for messages we sent — previously silently
                # ignored; now updates the matching WhatsAppMessageLog row.
                statuses = value.get("statuses", [])
                for st in statuses:
                    wa_message_id = st.get("id")
                    new_status = st.get("status")  # sent, delivered, read, failed
                    if not wa_message_id or not new_status:
                        continue
                    result = await db.execute(
                        select(WhatsAppMessageLog).where(WhatsAppMessageLog.wa_message_id == wa_message_id)
                    )
                    log_row = result.scalar_one_or_none()
                    if log_row:
                        log_row.status = new_status
                        log_row.status_updated_at = datetime.utcnow()
                    else:
                        logger.info(f"Received status update for untracked wa_message_id={wa_message_id}: {new_status}")

                await db.commit()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error parsing WhatsApp webhook: {e}")

    return {"status": "event_received"}


@router.post("/send", response_model=Dict[str, Any])
async def send_whatsapp_message(
    body: SendWAMessageBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Sends a text message using Meta WhatsApp Cloud API (per-org number if connected,
    else the global WHATSAPP_ACCESS_TOKEN/WHATSAPP_PHONE_NUMBER_ID fallback)."""
    try:
        data = await whatsapp_service.send_text(db, current_user.organization_id, body.to_number, body.message_text)
        await db.commit()
        return {"success": True, "data": data}
    except WhatsAppNotConfiguredError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except (CryptoNotConfiguredError, ValueError):
        raise HTTPException(status_code=503, detail="Stored credential could not be decrypted (encryption not configured, or ENCRYPTION_KEY was rotated).")
    except WhatsAppAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/send-template", response_model=Dict[str, Any])
async def send_whatsapp_template(
    body: SendWATemplateBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Sends a pre-registered Meta message template to client."""
    try:
        data = await whatsapp_service.send_template(db, current_user.organization_id, body.to_number, body.template_name, body.language_code)
        await db.commit()
        return {"success": True, "data": data}
    except WhatsAppNotConfiguredError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except (CryptoNotConfiguredError, ValueError):
        raise HTTPException(status_code=503, detail="Stored credential could not be decrypted (encryption not configured, or ENCRYPTION_KEY was rotated).")
    except WhatsAppAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/send-media", response_model=Dict[str, Any])
async def send_whatsapp_media(
    body: SendWAMediaBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Sends an image/video/document/audio message via a public link or a previously
    uploaded media_id (see POST /media/upload)."""
    try:
        data = await whatsapp_service.send_media(
            db, current_user.organization_id, body.to_number, body.media_type,
            link=body.link, media_id=body.media_id, caption=body.caption,
        )
        await db.commit()
        return {"success": True, "data": data}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except WhatsAppNotConfiguredError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except (CryptoNotConfiguredError, ValueError):
        raise HTTPException(status_code=503, detail="Stored credential could not be decrypted (encryption not configured, or ENCRYPTION_KEY was rotated).")
    except WhatsAppAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/media/upload", response_model=Dict[str, Any])
async def upload_whatsapp_media(
    filename: str,
    mime_type: str,
    content_base64: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Uploads media to the Cloud API's media store, returning a media_id usable with
    /send-media. Body carries base64-encoded bytes to keep this a plain JSON contract
    (no multipart form parsing needed here)."""
    try:
        file_bytes = base64.b64decode(content_base64)
    except Exception:
        raise HTTPException(status_code=400, detail="content_base64 is not valid base64.")

    try:
        media_id = await whatsapp_service.upload_media(db, current_user.organization_id, file_bytes, filename, mime_type)
        return {"media_id": media_id}
    except WhatsAppNotConfiguredError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except (CryptoNotConfiguredError, ValueError):
        raise HTTPException(status_code=503, detail="Stored credential could not be decrypted (encryption not configured, or ENCRYPTION_KEY was rotated).")
    except WhatsAppAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/media/{media_id}")
async def download_whatsapp_media(
    media_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Downloads and proxies real media bytes for a media_id (Meta's CDN URL requires the
    same bearer token, so the client can't fetch it directly)."""
    try:
        content, mime_type = await whatsapp_service.download_media(db, current_user.organization_id, media_id)
        return RawResponse(content=content, media_type=mime_type)
    except WhatsAppNotConfiguredError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except (CryptoNotConfiguredError, ValueError):
        raise HTTPException(status_code=503, detail="Stored credential could not be decrypted (encryption not configured, or ENCRYPTION_KEY was rotated).")
    except WhatsAppAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/phone-numbers/register", response_model=Dict[str, Any])
async def register_phone_number(
    body: RegisterPhoneNumberBody,
    current_user: User = Depends(require_whatsapp_write),
    db: AsyncSession = Depends(get_db),
):
    """Registers a new WhatsApp Business phone number for Cloud API use and stores it
    (encrypted access token) for this organization — real multi-number support."""
    try:
        await whatsapp_service.register_phone_number(db, current_user.organization_id, body.phone_number_id, body.access_token, body.pin)
        details = await whatsapp_service.fetch_phone_number_details(body.phone_number_id, body.access_token)
    except WhatsAppAPIError as e:
        raise HTTPException(status_code=502, detail=f"WhatsApp rejected the registration: {e}")

    result = await db.execute(
        select(WhatsAppPhoneNumber).where(
            WhatsAppPhoneNumber.organization_id == current_user.organization_id,
            WhatsAppPhoneNumber.phone_number_id == body.phone_number_id,
        )
    )
    row = result.scalar_one_or_none()
    if not row:
        row = WhatsAppPhoneNumber(organization_id=current_user.organization_id, phone_number_id=body.phone_number_id)
        db.add(row)

    try:
        row.access_token_encrypted = encrypt_value(body.access_token)
    except (CryptoNotConfiguredError, ValueError):
        raise HTTPException(status_code=503, detail="Stored credential could not be decrypted (encryption not configured, or ENCRYPTION_KEY was rotated).")

    row.display_phone_number = details.get("display_phone_number")
    row.verified_name = details.get("verified_name")
    row.quality_rating = details.get("quality_rating")
    row.status = "connected"
    row.last_error = None
    row.registered_at = datetime.utcnow()
    await db.commit()

    return {
        "phone_number_id": row.phone_number_id,
        "display_phone_number": row.display_phone_number,
        "verified_name": row.verified_name,
        "quality_rating": row.quality_rating,
        "status": row.status,
    }


@router.get("/phone-numbers", response_model=Dict[str, Any])
async def list_phone_numbers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists WhatsApp phone numbers registered for this organization."""
    result = await db.execute(select(WhatsAppPhoneNumber).where(WhatsAppPhoneNumber.organization_id == current_user.organization_id))
    rows = result.scalars().all()
    return {
        "phone_numbers": [
            {
                "id": r.id,
                "phone_number_id": r.phone_number_id,
                "display_phone_number": r.display_phone_number,
                "verified_name": r.verified_name,
                "quality_rating": r.quality_rating,
                "status": r.status,
                "last_error": r.last_error,
                "registered_at": r.registered_at.isoformat() if r.registered_at else None,
            }
            for r in rows
        ]
    }
