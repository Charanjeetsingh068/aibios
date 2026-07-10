import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import PermissionChecker
from app.core.database import get_db
from app.models.auth import User
from app.models.enterprise_integrations import LeadMapping, LeadSyncHistory

logger = logging.getLogger(__name__)
router = APIRouter()

require_integrations_read = PermissionChecker("integrations.read")
require_integrations_write = PermissionChecker("integrations.write")

class LeadMappingCreate(BaseModel):
    form_id: str
    meta_field: str
    crm_field: str


@router.get("/history", response_model=Dict[str, Any])
async def get_sync_history(
    current_user: User = Depends(require_integrations_read),
    db: AsyncSession = Depends(get_db)
):
    """Get the Meta Lead sync history for the organization."""
    result = await db.execute(
        select(LeadSyncHistory).where(LeadSyncHistory.organization_id == current_user.organization_id)
        .order_by(LeadSyncHistory.synced_at.desc()).limit(100)
    )
    history = result.scalars().all()
    return {"history": [{"id": h.id, "meta_lead_id": h.meta_lead_id, "status": h.status, "synced_at": h.synced_at} for h in history]}


@router.get("/mappings", response_model=Dict[str, Any])
async def list_lead_mappings(
    current_user: User = Depends(require_integrations_read),
    db: AsyncSession = Depends(get_db)
):
    """List custom Meta field mappings for the organization."""
    result = await db.execute(
        select(LeadMapping).where(LeadMapping.organization_id == current_user.organization_id)
    )
    mappings = result.scalars().all()
    return {"mappings": [{"id": m.id, "form_id": m.form_id, "meta_field": m.meta_field, "crm_field": m.crm_field} for m in mappings]}


@router.post("/mappings", response_model=Dict[str, Any])
async def create_lead_mapping(
    body: LeadMappingCreate,
    current_user: User = Depends(require_integrations_write),
    db: AsyncSession = Depends(get_db)
):
    """Create a custom Lead field mapping for Meta Webhooks."""
    mapping = LeadMapping(
        organization_id=current_user.organization_id,
        form_id=body.form_id,
        meta_field=body.meta_field,
        crm_field=body.crm_field
    )
    db.add(mapping)
    await db.commit()
    return {"status": "success", "id": mapping.id}


@router.delete("/mappings/{mapping_id}", response_model=Dict[str, Any])
async def delete_lead_mapping(
    mapping_id: str,
    current_user: User = Depends(require_integrations_write),
    db: AsyncSession = Depends(get_db)
):
    """Delete a custom Lead field mapping."""
    result = await db.execute(select(LeadMapping).where(LeadMapping.id == mapping_id, LeadMapping.organization_id == current_user.organization_id))
    mapping = result.scalar_one_or_none()
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
        
    await db.delete(mapping)
    await db.commit()
    return {"status": "success"}
