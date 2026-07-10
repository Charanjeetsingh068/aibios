import logging
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import PermissionChecker
from app.core.crypto import CryptoNotConfiguredError, decrypt_value, encrypt_value
from app.core.database import get_db
from app.models.auth import User
from app.models.enterprise_integrations import (
    IntegrationCredential,
    MetaLeadForm,
    MetaPage,
    OAuthSession,
)
from app.models.integrations import Integration
from app.services import meta_service
from app.services.meta_service import MetaAPIError, MetaNotConfiguredError

logger = logging.getLogger(__name__)
router = APIRouter()

require_meta_write = PermissionChecker("facebook.write")
require_integrations_read = PermissionChecker("integrations.read")


class OAuthCallbackBody(BaseModel):
    code: str


class SelectPagesBody(BaseModel):
    page_ids: List[str]


async def _get_meta_credential(db: AsyncSession, organization_id: str) -> Optional[IntegrationCredential]:
    result = await db.execute(
        select(IntegrationCredential).where(
            IntegrationCredential.organization_id == organization_id,
            IntegrationCredential.provider == "meta",
        )
    )
    return result.scalar_one_or_none()


async def _get_or_create_generic_integration(db: AsyncSession, organization_id: str, channel: str) -> Integration:
    result = await db.execute(
        select(Integration).where(Integration.organization_id == organization_id, Integration.channel == channel)
    )
    row = result.scalar_one_or_none()
    if not row:
        row = Integration(organization_id=organization_id, channel=channel, status="not_connected")
        db.add(row)
        await db.flush()
    return row


def _require_user_token(credential: Optional[IntegrationCredential]) -> str:
    if not credential or not credential.access_token_encrypted:
        raise HTTPException(status_code=409, detail="Meta is not connected for this organization yet. Complete the OAuth flow first.")
    try:
        return decrypt_value(credential.access_token_encrypted)
    except (CryptoNotConfiguredError, ValueError):
        raise HTTPException(status_code=503, detail="Stored credential could not be decrypted (encryption not configured, or ENCRYPTION_KEY was rotated).")
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/oauth/url", response_model=Dict[str, Any])
async def get_meta_oauth_url(current_user: User = Depends(require_meta_write), db: AsyncSession = Depends(get_db)):
    """Returns a real Meta OAuth dialog URL with business-integration scopes."""
    try:
        state = secrets.token_urlsafe(24)
        url = meta_service.build_oauth_url(state)
        
        session = OAuthSession(
            organization_id=current_user.organization_id,
            user_id=current_user.id,
            state=state,
            provider="facebook"
        )
        db.add(session)
        await db.commit()
        
        return {"url": url, "state": state}
    except MetaNotConfiguredError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/oauth/callback", response_model=Dict[str, Any])
async def meta_oauth_callback(
    body: OAuthCallbackBody,
    current_user: User = Depends(require_meta_write),
    db: AsyncSession = Depends(get_db),
):
    """Exchanges the OAuth code for a real long-lived user access token."""
    
    if body.state:
        res = await db.execute(select(OAuthSession).where(OAuthSession.state == body.state))
        session_row = res.scalar_one_or_none()
        if not session_row:
            raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
        if session_row.organization_id != current_user.organization_id:
            raise HTTPException(status_code=403, detail="State organization mismatch")
        await db.delete(session_row)
        await db.commit()

    try:
        short_lived = await meta_service.exchange_code_for_user_token(body.code)
        long_lived = await meta_service.exchange_for_long_lived_token(short_lived["access_token"])
    except MetaNotConfiguredError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except MetaAPIError as e:
        raise HTTPException(status_code=502, detail=f"Meta rejected the OAuth exchange: {e}")

    try:
        encrypted_token = encrypt_value(long_lived["access_token"])
    except (CryptoNotConfiguredError, ValueError):
        raise HTTPException(status_code=503, detail="Stored credential could not be decrypted (encryption not configured, or ENCRYPTION_KEY was rotated).")

    expires_in = long_lived.get("expires_in")
    expires_at = datetime.utcnow() + timedelta(seconds=int(expires_in)) if expires_in else None

    credential = await _get_meta_credential(db, current_user.organization_id)
    if not credential:
        credential = IntegrationCredential(organization_id=current_user.organization_id, provider="meta")
        db.add(credential)

    credential.access_token_encrypted = encrypted_token
    credential.token_type = long_lived.get("token_type", "bearer")
    credential.scope = ",".join(meta_service.META_BUSINESS_SCOPES)
    credential.expires_at = expires_at
    credential.status = "connected"
    credential.last_error = None
    credential.last_refreshed_at = datetime.utcnow()
    await db.flush()

    integration = await _get_or_create_generic_integration(db, current_user.organization_id, "facebook")
    integration.status = "connected"
    integration.external_account_id = credential.id
    integration.connected_at = datetime.utcnow()
    integration.token_expires_at = expires_at
    integration.detail = "OAuth user token acquired. Select pages to complete setup."
    await db.commit()

    return {
        "status": "connected",
        "expires_at": expires_at.isoformat() if expires_at else None,
        "next_step": "GET /integrations/meta/pages to discover manageable pages, then POST /integrations/meta/pages/select",
    }


@router.get("/pages", response_model=Dict[str, Any])
async def list_meta_pages(
    current_user: User = Depends(require_integrations_read),
    db: AsyncSession = Depends(get_db),
):
    """Lists the Facebook Pages the connected user manages (real Graph API call), for the
    caller to choose which to connect via POST /pages/select."""
    credential = await _get_meta_credential(db, current_user.organization_id)
    user_token = _require_user_token(credential)
    try:
        pages = await meta_service.list_managed_pages(user_token)
    except MetaAPIError as e:
        raise HTTPException(status_code=502, detail=f"Meta rejected the request: {e}")
    return {"pages": [{"id": p.get("id"), "name": p.get("name"), "category": p.get("category")} for p in pages]}


@router.post("/pages/select", response_model=Dict[str, Any])
async def select_meta_pages(
    body: SelectPagesBody,
    current_user: User = Depends(require_meta_write),
    db: AsyncSession = Depends(get_db),
):
    """Connects the selected Pages: stores each Page's own access token, subscribes the
    Page to the leadgen webhook, and resolves any linked Instagram Business account —
    the real, multi-page-capable replacement for the old fake connect_integration()."""
    credential = await _get_meta_credential(db, current_user.organization_id)
    user_token = _require_user_token(credential)
    try:
        managed_pages = await meta_service.list_managed_pages(user_token)
    except MetaAPIError as e:
        raise HTTPException(status_code=502, detail=f"Meta rejected the request: {e}")

    managed_by_id = {p.get("id"): p for p in managed_pages}
    connected: List[Dict[str, Any]] = []
    any_instagram = False

    for page_id in body.page_ids:
        page_info = managed_by_id.get(page_id)
        if not page_info:
            connected.append({"id": page_id, "status": "error", "detail": "Page not found among pages this user manages."})
            continue

        page_token = page_info.get("access_token")
        result = await db.execute(
            select(MetaPage).where(MetaPage.organization_id == current_user.organization_id, MetaPage.page_id == page_id)
        )
        page_row = result.scalar_one_or_none()
        if not page_row:
            page_row = MetaPage(organization_id=current_user.organization_id, page_id=page_id, credential_id=credential.id if credential else None)
            db.add(page_row)

        try:
            page_row.page_access_token_encrypted = encrypt_value(page_token)
        except (CryptoNotConfiguredError, ValueError):
            raise HTTPException(status_code=503, detail="Stored credential could not be decrypted (encryption not configured, or ENCRYPTION_KEY was rotated).")

        page_row.page_name = page_info.get("name")
        page_row.category = page_info.get("category")
        page_row.status = "connected"
        page_row.connected_at = datetime.utcnow()

        try:
            await meta_service.subscribe_page_webhook(page_id, page_token)
            page_row.webhook_subscribed = True
            page_row.last_error = None
        except MetaAPIError as e:
            page_row.webhook_subscribed = False
            page_row.status = "error"
            page_row.last_error = f"Webhook subscription failed: {e}"

        try:
            ig = await meta_service.get_instagram_business_account(page_id, page_token)
            if ig:
                page_row.instagram_business_account_id = ig.get("id")
                page_row.instagram_username = ig.get("username")
                any_instagram = True
        except MetaAPIError as e:
            logger.warning(f"Could not resolve Instagram Business account for page {page_id}: {e}")

        connected.append({
            "id": page_id,
            "status": page_row.status,
            "webhook_subscribed": page_row.webhook_subscribed,
            "instagram_business_account_id": page_row.instagram_business_account_id,
        })

    fb_integration = await _get_or_create_generic_integration(db, current_user.organization_id, "facebook")
    fb_integration.status = "connected"
    fb_integration.external_account_id = ",".join(body.page_ids)
    fb_integration.connected_at = datetime.utcnow()
    fb_integration.last_synced_at = datetime.utcnow()
    fb_integration.detail = f"{len(body.page_ids)} page(s) connected."

    if any_instagram:
        ig_integration = await _get_or_create_generic_integration(db, current_user.organization_id, "instagram")
        ig_integration.status = "connected"
        ig_integration.connected_at = datetime.utcnow()
        ig_integration.last_synced_at = datetime.utcnow()
        ig_integration.detail = "Connected via linked Facebook Page."

    await db.commit()
    return {"pages": connected}


@router.get("/pages/{page_id}/lead-forms", response_model=Dict[str, Any])
async def list_lead_forms(
    page_id: str,
    current_user: User = Depends(require_integrations_read),
    db: AsyncSession = Depends(get_db),
):
    """Discovers and persists Lead Ads forms configured on a connected Page."""
    result = await db.execute(
        select(MetaPage).where(MetaPage.organization_id == current_user.organization_id, MetaPage.page_id == page_id)
    )
    page_row = result.scalar_one_or_none()
    if not page_row or not page_row.page_access_token_encrypted:
        raise HTTPException(status_code=404, detail="Page is not connected for this organization.")

    try:
        page_token = decrypt_value(page_row.page_access_token_encrypted)
        forms = await meta_service.list_lead_forms(page_id, page_token)
    except (CryptoNotConfiguredError, ValueError):
        raise HTTPException(status_code=503, detail="Stored credential could not be decrypted (encryption not configured, or ENCRYPTION_KEY was rotated).")
    except MetaAPIError as e:
        raise HTTPException(status_code=502, detail=f"Meta rejected the request: {e}")

    for form in forms:
        result = await db.execute(
            select(MetaLeadForm).where(MetaLeadForm.meta_page_id == page_row.id, MetaLeadForm.form_id == form.get("id"))
        )
        form_row = result.scalar_one_or_none()
        if not form_row:
            form_row = MetaLeadForm(organization_id=current_user.organization_id, meta_page_id=page_row.id, form_id=form.get("id"))
            db.add(form_row)
        form_row.form_name = form.get("name")
        form_row.status = form.get("status")
        form_row.discovered_at = datetime.utcnow()
    await db.commit()

    return {"lead_forms": forms}


@router.post("/pages/{page_id}/webhook/resubscribe", response_model=Dict[str, Any])
async def resubscribe_page_webhook(
    page_id: str,
    current_user: User = Depends(require_meta_write),
    db: AsyncSession = Depends(get_db),
):
    """Error-recovery path: re-subscribes a connected Page to the leadgen webhook, e.g.
    after Meta reports the subscription was dropped."""
    result = await db.execute(
        select(MetaPage).where(MetaPage.organization_id == current_user.organization_id, MetaPage.page_id == page_id)
    )
    page_row = result.scalar_one_or_none()
    if not page_row or not page_row.page_access_token_encrypted:
        raise HTTPException(status_code=404, detail="Page is not connected for this organization.")

    try:
        page_token = decrypt_value(page_row.page_access_token_encrypted)
        await meta_service.subscribe_page_webhook(page_id, page_token)
    except (CryptoNotConfiguredError, ValueError):
        raise HTTPException(status_code=503, detail="Stored credential could not be decrypted (encryption not configured, or ENCRYPTION_KEY was rotated).")
    except MetaAPIError as e:
        page_row.webhook_subscribed = False
        page_row.status = "error"
        page_row.last_error = f"Webhook subscription failed: {e}"
        await db.commit()
        raise HTTPException(status_code=502, detail=f"Meta rejected the webhook subscription: {e}")

    page_row.webhook_subscribed = True
    page_row.status = "connected"
    page_row.last_error = None
    await db.commit()
    return {"page_id": page_id, "webhook_subscribed": True}
