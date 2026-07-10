import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import CryptoNotConfiguredError, decrypt_value
from app.models.enterprise_integrations import (
    IntegrationCredential,
    MetaPage,
    VoiceProviderCredential,
    WhatsAppPhoneNumber,
)
from app.models.integrations import Integration
from app.services import meta_service
from app.services.meta_service import MetaAPIError

logger = logging.getLogger(__name__)

EXPIRES_SOON_WINDOW = timedelta(days=7)


def _health_row(provider: str, resource_type: str, resource_id: str, status: str,
                 token_expires_at: Optional[datetime], last_error: Optional[str],
                 last_synced_at: Optional[datetime]) -> Dict[str, Any]:
    expires_soon = bool(token_expires_at and token_expires_at - datetime.utcnow() < EXPIRES_SOON_WINDOW)
    return {
        "provider": provider,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "status": status,
        "token_expires_at": token_expires_at.isoformat() if token_expires_at else None,
        "expires_soon": expires_soon,
        "last_error": last_error,
        "last_synced_at": last_synced_at.isoformat() if last_synced_at else None,
    }


async def get_health(db: AsyncSession, organization_id: str) -> List[Dict[str, Any]]:
    """Aggregates health across every connected integration surface for an organization:
    generic channel-status rows, Meta Pages, WhatsApp phone numbers, AI voice provider
    credentials, and the n8n connection."""
    rows: List[Dict[str, Any]] = []

    result = await db.execute(select(Integration).where(Integration.organization_id == organization_id))
    for i in result.scalars().all():
        rows.append(_health_row(i.channel, "integration", i.id, i.status, i.token_expires_at, i.detail if i.status == "error" else None, i.last_synced_at))

    result = await db.execute(select(MetaPage).where(MetaPage.organization_id == organization_id))
    for p in result.scalars().all():
        rows.append(_health_row("meta_page", "meta_page", p.id, p.status, None, p.last_error, p.connected_at))

    result = await db.execute(select(WhatsAppPhoneNumber).where(WhatsAppPhoneNumber.organization_id == organization_id))
    for w in result.scalars().all():
        rows.append(_health_row("whatsapp_phone_number", "whatsapp_phone_number", w.id, w.status, None, w.last_error, w.registered_at))

    result = await db.execute(select(VoiceProviderCredential).where(VoiceProviderCredential.organization_id == organization_id))
    for v in result.scalars().all():
        rows.append(_health_row(v.provider, "voice_provider_credential", v.id, v.status, None, v.last_error, None))



    return rows


async def refresh_meta_credential(db: AsyncSession, credential: IntegrationCredential) -> IntegrationCredential:
    """Refreshes a Meta long-lived user token. Never raises to the caller — failures are
    recorded on the credential row (status=error, last_error) so the caller can report
    honest health rather than crashing the refresh sweep."""
    if not credential.access_token_encrypted:
        credential.status = "error"
        credential.last_error = "No access token stored to refresh."
        return credential
    try:
        current_token = decrypt_value(credential.access_token_encrypted)
        refreshed = await meta_service.exchange_for_long_lived_token(current_token)
        from app.core.crypto import encrypt_value
        credential.access_token_encrypted = encrypt_value(refreshed["access_token"])
        expires_in = refreshed.get("expires_in")
        credential.expires_at = datetime.utcnow() + timedelta(seconds=int(expires_in)) if expires_in else None
        credential.status = "connected"
        credential.last_error = None
        credential.last_refreshed_at = datetime.utcnow()
    except (CryptoNotConfiguredError, ValueError) as e:
        credential.status = "error"
        credential.last_error = str(e)
    except MetaAPIError as e:
        credential.status = "error"
        credential.last_error = f"Token refresh failed: {e}"
        logger.warning(f"Meta token refresh failed for credential {credential.id}: {e}")
    return credential


_RESOURCE_TABLES = {
    "integration": Integration,
    "integration_credential": IntegrationCredential,
    "meta_page": MetaPage,
    "whatsapp_phone_number": WhatsAppPhoneNumber,
    "voice_provider_credential": VoiceProviderCredential,

}


async def disconnect(db: AsyncSession, organization_id: str, resource_type: str, resource_id: str) -> Dict[str, Any]:
    """Disconnects a resource: revokes upstream where the API supports it (Meta), then
    clears the local row. Returns a status dict rather than raising on partial failure —
    local disconnect always succeeds even if the upstream revoke call fails."""
    model = _RESOURCE_TABLES.get(resource_type)
    if not model:
        raise ValueError(f"Unknown resource_type '{resource_type}'. Valid: {list(_RESOURCE_TABLES.keys())}")

    row = await db.get(model, resource_id)
    if not row or row.organization_id != organization_id:
        raise LookupError("Resource not found for this organization.")

    revoke_warning = None
    if resource_type == "meta_page" and getattr(row, "page_access_token_encrypted", None):
        try:
            page_token = decrypt_value(row.page_access_token_encrypted)
            # Pages don't have a per-user /permissions revoke; best-effort unsubscribe instead.
            await meta_service.subscribe_page_webhook(row.page_id, page_token, fields="")
        except Exception as e:
            revoke_warning = f"Upstream unsubscribe failed (local disconnect proceeded anyway): {e}"
            logger.warning(revoke_warning)

    if hasattr(row, "status"):
        row.status = "disconnected"
    await db.commit()

    return {"resource_type": resource_type, "resource_id": resource_id, "status": "disconnected", "warning": revoke_warning}


async def retry(db: AsyncSession, organization_id: str, resource_type: str, resource_id: str) -> Dict[str, Any]:
    """Error-recovery: clears the last_error on a resource so the next real operation
    (webhook, send, sync) gets a clean slate — does not fabricate success. The caller
    (e.g. meta_integration.py's resubscribe endpoint) performs the actual retried operation;
    this just resets bookkeeping and reports current status."""
    model = _RESOURCE_TABLES.get(resource_type)
    if not model:
        raise ValueError(f"Unknown resource_type '{resource_type}'. Valid: {list(_RESOURCE_TABLES.keys())}")

    row = await db.get(model, resource_id)
    if not row or row.organization_id != organization_id:
        raise LookupError("Resource not found for this organization.")

    if hasattr(row, "last_error"):
        row.last_error = None
    if hasattr(row, "detail") and getattr(row, "status", None) == "error":
        row.detail = None
    await db.commit()

    return {"resource_type": resource_type, "resource_id": resource_id, "status": getattr(row, "status", None)}
