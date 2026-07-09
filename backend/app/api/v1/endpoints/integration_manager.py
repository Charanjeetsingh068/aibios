import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.crypto import CryptoNotConfiguredError
from app.api.v1.endpoints.auth import get_current_user, PermissionChecker
from app.models.auth import User
from app.models.enterprise_integrations import IntegrationCredential
from app.services import integration_manager

logger = logging.getLogger(__name__)
router = APIRouter()

require_integrations_write = PermissionChecker("integrations.write")
require_integrations_read = PermissionChecker("integrations.read")


@router.get("/health", response_model=Dict[str, Any])
async def get_integration_health(
    current_user: User = Depends(require_integrations_read),
    db: AsyncSession = Depends(get_db),
):
    """Aggregated health across every connected integration surface (generic channel
    status, Meta Pages, WhatsApp numbers, AI voice providers, n8n) for this organization."""
    return {"resources": await integration_manager.get_health(db, current_user.organization_id)}


@router.post("/{resource_type}/{resource_id}/refresh", response_model=Dict[str, Any])
async def refresh_resource(
    resource_type: str,
    resource_id: str,
    current_user: User = Depends(require_integrations_write),
    db: AsyncSession = Depends(get_db),
):
    """Manual token-refresh (error-recovery path). Currently supports Meta
    (resource_type=integration_credential, provider=meta) — other providers either don't
    issue refreshable tokens (WhatsApp/voice API keys are static) or aren't OAuth-based."""
    if resource_type != "integration_credential":
        raise HTTPException(status_code=400, detail="Only resource_type=integration_credential (Meta OAuth tokens) supports refresh.")

    credential = await db.get(IntegrationCredential, resource_id)
    if not credential or credential.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Credential not found for this organization.")
    if credential.provider != "meta":
        raise HTTPException(status_code=400, detail=f"Refresh is not supported for provider '{credential.provider}'.")

    try:
        await integration_manager.refresh_meta_credential(db, credential)
        await db.commit()
    except (CryptoNotConfiguredError, ValueError):
        raise HTTPException(status_code=503, detail="Stored credential could not be decrypted (encryption not configured, or ENCRYPTION_KEY was rotated).")

    return {
        "resource_id": credential.id,
        "status": credential.status,
        "last_error": credential.last_error,
        "expires_at": credential.expires_at.isoformat() if credential.expires_at else None,
    }


@router.post("/{resource_type}/{resource_id}/retry", response_model=Dict[str, Any])
async def retry_resource(
    resource_type: str,
    resource_id: str,
    current_user: User = Depends(require_integrations_write),
    db: AsyncSession = Depends(get_db),
):
    """Clears a resource's error state so the next real operation gets a clean slate."""
    try:
        return await integration_manager.retry(db, current_user.organization_id, resource_type, resource_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{resource_type}/{resource_id}/disconnect", response_model=Dict[str, Any])
async def disconnect_resource(
    resource_type: str,
    resource_id: str,
    current_user: User = Depends(require_integrations_write),
    db: AsyncSession = Depends(get_db),
):
    """Disconnects a resource: revokes upstream where supported, then clears the local row."""
    try:
        return await integration_manager.disconnect(db, current_user.organization_id, resource_type, resource_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{resource_type}/{resource_id}/sync-status", response_model=Dict[str, Any])
async def get_sync_status(
    resource_type: str,
    resource_id: str,
    current_user: User = Depends(require_integrations_read),
    db: AsyncSession = Depends(get_db),
):
    """Returns last_synced_at/last_error for a single resource, without recomputing the
    full cross-provider health list."""
    health = await integration_manager.get_health(db, current_user.organization_id)
    for row in health:
        if row["resource_type"] == resource_type and row["resource_id"] == resource_id:
            return row
    raise HTTPException(status_code=404, detail="Resource not found for this organization.")
