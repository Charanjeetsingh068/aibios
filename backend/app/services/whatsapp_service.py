import logging
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings
from app.core.crypto import decrypt_value, CryptoNotConfiguredError
from app.models.enterprise_integrations import WhatsAppPhoneNumber, WhatsAppMessageLog

logger = logging.getLogger(__name__)

GRAPH_API_VERSION = "v18.0"
GRAPH_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"
REQUEST_TIMEOUT_SECONDS = 15.0
RETRYABLE_EXCEPTIONS = (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout)


class WhatsAppNotConfiguredError(Exception):
    """Raised when no phone number is configured for this organization (neither a
    per-org WhatsAppPhoneNumber row nor the global settings.WHATSAPP_* fallback)."""


class WhatsAppAPIError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


async def resolve_credentials(db: AsyncSession, organization_id: str) -> Tuple[str, str, Optional[WhatsAppPhoneNumber]]:
    """Resolves (phone_number_id, access_token, phone_row) for an organization: prefers a
    connected per-org WhatsAppPhoneNumber row, falling back to the global
    settings.WHATSAPP_PHONE_NUMBER_ID/WHATSAPP_ACCESS_TOKEN (backward-compatible with the
    original single-tenant, env-var-only setup)."""
    result = await db.execute(
        select(WhatsAppPhoneNumber).where(
            WhatsAppPhoneNumber.organization_id == organization_id,
            WhatsAppPhoneNumber.status == "connected",
        ).order_by(WhatsAppPhoneNumber.created_at.asc())
    )
    row = result.scalars().first()
    if row:
        if row.access_token_encrypted:
            try:
                return row.phone_number_id, decrypt_value(row.access_token_encrypted), row
            except CryptoNotConfiguredError:
                raise
        if settings.WHATSAPP_ACCESS_TOKEN:
            return row.phone_number_id, settings.WHATSAPP_ACCESS_TOKEN, row

    if settings.WHATSAPP_ACCESS_TOKEN and settings.WHATSAPP_PHONE_NUMBER_ID:
        return settings.WHATSAPP_PHONE_NUMBER_ID, settings.WHATSAPP_ACCESS_TOKEN, None

    raise WhatsAppNotConfiguredError(
        "WhatsApp is not configured for this organization (no connected phone number, and "
        "no WHATSAPP_ACCESS_TOKEN/WHATSAPP_PHONE_NUMBER_ID fallback set)."
    )


@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
)
async def _graph_post_json(phone_number_id: str, access_token: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        res = await client.post(
            f"{GRAPH_API_BASE}/{phone_number_id}/messages",
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
            json=payload,
        )
    body = res.json() if res.content else {}
    if res.status_code != 200:
        raise WhatsAppAPIError(body.get("error", {}).get("message", res.text), status_code=res.status_code)
    return body


async def _log_message(
    db: AsyncSession,
    organization_id: str,
    phone_row: Optional[WhatsAppPhoneNumber],
    *,
    wa_message_id: Optional[str],
    direction: str,
    to_number: Optional[str] = None,
    from_number: Optional[str] = None,
    message_type: str = "text",
    template_name: Optional[str] = None,
    media_id: Optional[str] = None,
    status: str = "sent",
    lead_id: Optional[str] = None,
    raw_payload: Optional[str] = None,
) -> WhatsAppMessageLog:
    log = WhatsAppMessageLog(
        organization_id=organization_id,
        phone_number_row_id=phone_row.id if phone_row else None,
        wa_message_id=wa_message_id,
        direction=direction,
        to_number=to_number,
        from_number=from_number,
        message_type=message_type,
        template_name=template_name,
        media_id=media_id,
        status=status,
        status_updated_at=datetime.utcnow(),
        lead_id=lead_id,
        raw_payload=raw_payload,
    )
    db.add(log)
    await db.flush()
    return log


async def send_text(db: AsyncSession, organization_id: str, to_number: str, message_text: str) -> Dict[str, Any]:
    phone_number_id, token, phone_row = await resolve_credentials(db, organization_id)
    body = await _graph_post_json(phone_number_id, token, {
        "messaging_product": "whatsapp", "to": to_number, "type": "text", "text": {"body": message_text},
    })
    wa_message_id = (body.get("messages") or [{}])[0].get("id")
    await _log_message(db, organization_id, phone_row, wa_message_id=wa_message_id, direction="outbound",
                        to_number=to_number, message_type="text", status="sent")
    return body


async def send_template(db: AsyncSession, organization_id: str, to_number: str, template_name: str, language_code: str = "en") -> Dict[str, Any]:
    phone_number_id, token, phone_row = await resolve_credentials(db, organization_id)
    body = await _graph_post_json(phone_number_id, token, {
        "messaging_product": "whatsapp", "to": to_number, "type": "template",
        "template": {"name": template_name, "language": {"code": language_code}},
    })
    wa_message_id = (body.get("messages") or [{}])[0].get("id")
    await _log_message(db, organization_id, phone_row, wa_message_id=wa_message_id, direction="outbound",
                        to_number=to_number, message_type="template", template_name=template_name, status="sent")
    return body


async def send_media(db: AsyncSession, organization_id: str, to_number: str, media_type: str, link: Optional[str] = None, media_id: Optional[str] = None, caption: Optional[str] = None) -> Dict[str, Any]:
    """Sends an image/video/document/audio message, either by a public `link` or a
    previously-uploaded `media_id` (exactly one must be provided, per the Cloud API contract)."""
    if media_type not in ("image", "video", "document", "audio"):
        raise ValueError(f"Unsupported media_type: {media_type}")
    if not link and not media_id:
        raise ValueError("Either link or media_id must be provided.")

    media_object: Dict[str, Any] = {"link": link} if link else {"id": media_id}
    if caption and media_type in ("image", "video", "document"):
        media_object["caption"] = caption

    phone_number_id, token, phone_row = await resolve_credentials(db, organization_id)
    body = await _graph_post_json(phone_number_id, token, {
        "messaging_product": "whatsapp", "to": to_number, "type": media_type, media_type: media_object,
    })
    wa_message_id = (body.get("messages") or [{}])[0].get("id")
    await _log_message(db, organization_id, phone_row, wa_message_id=wa_message_id, direction="outbound",
                        to_number=to_number, message_type=media_type, media_id=media_id, status="sent")
    return body


async def mark_as_read(db: AsyncSession, organization_id: str, wa_message_id: str) -> Dict[str, Any]:
    phone_number_id, token, _phone_row = await resolve_credentials(db, organization_id)
    return await _graph_post_json(phone_number_id, token, {
        "messaging_product": "whatsapp", "status": "read", "message_id": wa_message_id,
    })


@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
)
async def upload_media(db: AsyncSession, organization_id: str, file_bytes: bytes, filename: str, mime_type: str) -> str:
    """Uploads media to the Cloud API's media store, returning a media_id usable by
    send_media(). Real multipart upload per Meta's documented contract."""
    phone_number_id, token, _phone_row = await resolve_credentials(db, organization_id)
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        res = await client.post(
            f"{GRAPH_API_BASE}/{phone_number_id}/media",
            headers={"Authorization": f"Bearer {token}"},
            data={"messaging_product": "whatsapp"},
            files={"file": (filename, file_bytes, mime_type)},
        )
    body = res.json() if res.content else {}
    if res.status_code != 200 or "id" not in body:
        raise WhatsAppAPIError(body.get("error", {}).get("message", res.text), status_code=res.status_code)
    return body["id"]


async def get_media_url(db: AsyncSession, organization_id: str, media_id: str) -> Dict[str, Any]:
    """Resolves a media_id to its (short-lived, auth-required) download URL + metadata."""
    phone_number_id, token, _phone_row = await resolve_credentials(db, organization_id)
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        res = await client.get(f"{GRAPH_API_BASE}/{media_id}", headers={"Authorization": f"Bearer {token}"})
    body = res.json() if res.content else {}
    if res.status_code != 200:
        raise WhatsAppAPIError(body.get("error", {}).get("message", res.text), status_code=res.status_code)
    return body


async def download_media(db: AsyncSession, organization_id: str, media_id: str) -> Tuple[bytes, str]:
    """Downloads the actual media bytes for a media_id. Meta's CDN URL still requires the
    Authorization bearer header, so this can't be a plain redirect."""
    phone_number_id, token, _phone_row = await resolve_credentials(db, organization_id)
    meta = await get_media_url(db, organization_id, media_id)
    url = meta.get("url")
    mime_type = meta.get("mime_type", "application/octet-stream")
    if not url:
        raise WhatsAppAPIError("Media metadata did not include a download URL.")
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        res = await client.get(url, headers={"Authorization": f"Bearer {token}"})
    if res.status_code != 200:
        raise WhatsAppAPIError(f"Failed to download media: HTTP {res.status_code}", status_code=res.status_code)
    return res.content, mime_type


async def register_phone_number(db: AsyncSession, organization_id: str, phone_number_id: str, access_token: str, pin: str) -> Dict[str, Any]:
    """Registers a WhatsApp Business phone number for Cloud API use (real
    POST /{phone-number-id}/register call — required before a newly-added number can
    send/receive messages)."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        res = await client.post(
            f"{GRAPH_API_BASE}/{phone_number_id}/register",
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
            json={"messaging_product": "whatsapp", "pin": pin},
        )
    body = res.json() if res.content else {}
    if res.status_code != 200:
        raise WhatsAppAPIError(body.get("error", {}).get("message", res.text), status_code=res.status_code)
    return body


async def fetch_phone_number_details(phone_number_id: str, access_token: str) -> Dict[str, Any]:
    """Fetches verified name / quality rating for a registered phone number."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        res = await client.get(
            f"{GRAPH_API_BASE}/{phone_number_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"fields": "verified_name,display_phone_number,quality_rating"},
        )
    body = res.json() if res.content else {}
    if res.status_code != 200:
        raise WhatsAppAPIError(body.get("error", {}).get("message", res.text), status_code=res.status_code)
    return body
