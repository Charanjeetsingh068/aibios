import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import PermissionChecker
from app.core.audit import record_audit_log
from app.core.database import get_db, mongo_db
from app.core.realtime import emit_to_organization
from app.models.auth import User
from app.models.business import Lead
from app.schemas.leads import (
    VALID_SOURCES,
    VALID_STATUSES,
    LeadCreate,
    LeadEventCreate,
    LeadUpdate,
)
from app.services.event_bus import dispatch_event

require_crm_read = PermissionChecker("crm.read")
require_crm_write = PermissionChecker("crm.write")
require_crm_delete = PermissionChecker("crm.delete")

logger = logging.getLogger(__name__)
router = APIRouter()

SOURCE_COLLECTIONS = {
    "facebook": "facebook_leads",
    "instagram": "instagram_leads",
    "whatsapp": "whatsapp_leads",
}


def _serialize(lead: Lead) -> Dict[str, Any]:
    return {
        "id": lead.id,
        "organization_id": lead.organization_id,
        "name": lead.name,
        "company": lead.company,
        "phone": lead.phone,
        "email": lead.email,
        "source": lead.source,
        "status": lead.status,
        "value": float(lead.value or 0),
        "campaign_id": lead.campaign_id,
        "assigned_to": lead.assigned_to,
        "created_at": lead.created_at.isoformat() if lead.created_at else None,
        "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
    }


async def _record_mongo_lead(lead: Lead, raw_payload: Optional[dict] = None) -> None:
    """Mirrors the lead into MongoDB per the spec's per-channel + all_leads collections."""
    try:
        doc = {**_serialize(lead), "raw_payload": raw_payload or {}}
        await asyncio.wait_for(
            mongo_db["all_leads"].update_one({"_id": lead.id}, {"$set": {**doc, "_id": lead.id}}, upsert=True),
            timeout=1.5
        )
        channel_collection = SOURCE_COLLECTIONS.get(lead.source)
        if channel_collection:
            await asyncio.wait_for(
                mongo_db[channel_collection].update_one({"_id": lead.id}, {"$set": {**doc, "_id": lead.id}}, upsert=True),
                timeout=1.5
            )
    except Exception as e:
        logger.error(f"MongoDB mirroring skipped (offline/timeout): {e}")


async def _record_lead_event(lead_id: str, organization_id: str, event_type: str, note: str, actor_user_id: Optional[str] = None) -> None:
    try:
        await asyncio.wait_for(
            mongo_db["lead_events"].insert_one({
                "lead_id": lead_id,
                "organization_id": organization_id,
                "type": event_type,
                "note": note,
                "actor_user_id": actor_user_id,
                "created_at": datetime.utcnow(),
            }),
            timeout=1.5
        )
    except Exception as e:
        logger.error(f"MongoDB event logging skipped (offline/timeout): {e}")


@router.get("", response_model=Dict[str, Any])
async def list_leads(
    status_filter: Optional[str] = Query(None, alias="status"),
    source: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_crm_read),
    db: AsyncSession = Depends(get_db),
):
    query = select(Lead).where(Lead.organization_id == current_user.organization_id)
    count_query = select(func.count(Lead.id)).where(Lead.organization_id == current_user.organization_id)

    if status_filter:
        query = query.where(Lead.status == status_filter)
        count_query = count_query.where(Lead.status == status_filter)
    if source:
        query = query.where(Lead.source == source)
        count_query = count_query.where(Lead.source == source)
    if search:
        like = f"%{search}%"
        query = query.where(Lead.name.ilike(like))
        count_query = count_query.where(Lead.name.ilike(like))

    query = query.order_by(Lead.created_at.desc()).limit(limit).offset(offset)

    result = await db.execute(query)
    leads = result.scalars().all()
    total = (await db.execute(count_query)).scalar() or 0

    return {"leads": [_serialize(l) for l in leads], "total": total}


@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_lead(
    body: LeadCreate,
    request: Request,
    current_user: User = Depends(require_crm_write),
    db: AsyncSession = Depends(get_db),
):
    if body.source not in VALID_SOURCES:
        raise HTTPException(status_code=400, detail=f"Invalid source. Must be one of {sorted(VALID_SOURCES)}")

    lead = Lead(
        organization_id=current_user.organization_id,
        name=body.name.strip(),
        company=body.company,
        phone=body.phone,
        email=body.email,
        source=body.source,
        value=body.value,
        campaign_id=body.campaign_id,
        status="new",
        created_by=current_user.id,
        updated_by=current_user.id,
    )
    db.add(lead)
    await db.flush()
    await record_audit_log(
        db, actor=current_user, organization_id=lead.organization_id, action="lead.create",
        description=f"Lead '{lead.name}' created via {lead.source}", resource="leads", resource_id=lead.id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(lead)

    await _record_mongo_lead(lead)
    await _record_lead_event(lead.id, lead.organization_id, "created", f"Lead created via {lead.source}", current_user.id)
    await dispatch_event(db, lead.organization_id, "lead.created", {
        "lead_id": lead.id, "name": lead.name, "email": lead.email, "phone": lead.phone, "source": lead.source,
    })

    payload = _serialize(lead)
    await emit_to_organization(lead.organization_id, "lead:new", payload)
    return payload


@router.get("/{lead_id}", response_model=Dict[str, Any])
async def get_lead(
    lead_id: str,
    current_user: User = Depends(require_crm_read),
    db: AsyncSession = Depends(get_db),
):
    lead = await db.get(Lead, lead_id)
    if not lead or lead.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Lead not found")
    return _serialize(lead)


@router.patch("/{lead_id}", response_model=Dict[str, Any])
async def update_lead(
    lead_id: str,
    body: LeadUpdate,
    request: Request,
    current_user: User = Depends(require_crm_write),
    db: AsyncSession = Depends(get_db),
):
    lead = await db.get(Lead, lead_id)
    if not lead or lead.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Lead not found")

    if body.status is not None and body.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {sorted(VALID_STATUSES)}")

    changes = body.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(lead, field, value)
    lead.updated_by = current_user.id

    await record_audit_log(
        db, actor=current_user, organization_id=lead.organization_id, action="lead.update",
        description=f"Lead '{lead.name}' updated ({', '.join(changes.keys()) or 'no fields'})", resource="leads", resource_id=lead.id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(lead)

    await _record_mongo_lead(lead)
    if "status" in changes:
        await _record_lead_event(lead.id, lead.organization_id, "status_changed", f"Status changed to {lead.status}", current_user.id)

    payload = _serialize(lead)
    await emit_to_organization(lead.organization_id, "lead:updated", payload)
    return payload


@router.delete("/{lead_id}", response_model=Dict[str, Any])
async def delete_lead(
    lead_id: str,
    request: Request,
    current_user: User = Depends(require_crm_delete),
    db: AsyncSession = Depends(get_db),
):
    lead = await db.get(Lead, lead_id)
    if not lead or lead.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Lead not found")

    await record_audit_log(
        db, actor=current_user, organization_id=lead.organization_id, action="lead.delete",
        description=f"Lead '{lead.name}' deleted", resource="leads", resource_id=lead.id,
        ip_address=request.client.host if request.client else None,
    )
    await db.delete(lead)
    await db.commit()

    await mongo_db["all_leads"].delete_one({"_id": lead_id})
    for collection in SOURCE_COLLECTIONS.values():
        await mongo_db[collection].delete_one({"_id": lead_id})

    await emit_to_organization(current_user.organization_id, "lead:deleted", {"id": lead_id})
    return {"success": True}


@router.get("/{lead_id}/events", response_model=Dict[str, Any])
async def get_lead_events(
    lead_id: str,
    current_user: User = Depends(require_crm_read),
    db: AsyncSession = Depends(get_db),
):
    lead = await db.get(Lead, lead_id)
    if not lead or lead.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Lead not found")

    events: List[Dict[str, Any]] = []
    try:
        cursor = mongo_db["lead_events"].find({"lead_id": lead_id}).sort("created_at", -1).limit(200)
        docs = await asyncio.wait_for(cursor.to_list(length=200), timeout=1.5)
        for doc in docs:
            events.append({
                "id": str(doc["_id"]),
                "type": doc.get("type"),
                "note": doc.get("note"),
                "actor_user_id": doc.get("actor_user_id"),
                "created_at": doc["created_at"].isoformat() if doc.get("created_at") else None,
            })
    except Exception as e:
        logger.error(f"MongoDB lead events query skipped (offline/timeout): {e}")
    return {"events": events}


@router.post("/{lead_id}/events", response_model=Dict[str, Any])
async def add_lead_event(
    lead_id: str,
    body: LeadEventCreate,
    current_user: User = Depends(require_crm_write),
    db: AsyncSession = Depends(get_db),
):
    lead = await db.get(Lead, lead_id)
    if not lead or lead.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Lead not found")

    await _record_lead_event(lead_id, lead.organization_id, body.type, body.note, current_user.id)
    return {"success": True}


# ---------------------------------------------------------
# NEW PHASE 5.4 ROUTES: Bulk Actions, Merge, Sub-resources
# ---------------------------------------------------------

from app.models.business import LeadHistory, LeadNote, LeadTag, Tag
from app.schemas.leads import (
    LeadBulkUpdate,
    LeadMergeRequest,
    LeadNoteCreate,
    LeadNoteResponse,
    TagCreate,
    TagResponse,
)


@router.post("/bulk/update", response_model=Dict[str, Any])
async def bulk_update_leads(
    body: LeadBulkUpdate,
    current_user: User = Depends(require_crm_write),
    db: AsyncSession = Depends(get_db),
):
    query = select(Lead).where(Lead.id.in_(body.lead_ids), Lead.organization_id == current_user.organization_id)
    result = await db.execute(query)
    leads = result.scalars().all()
    
    for lead in leads:
        if body.status is not None:
            lead.status = body.status
        if body.assigned_to is not None:
            lead.assigned_to = body.assigned_to
        if body.campaign_id is not None:
            lead.campaign_id = body.campaign_id
        lead.updated_by = current_user.id
        
    await db.commit()
    return {"updated": len(leads)}

@router.post("/bulk/delete", response_model=Dict[str, Any])
async def bulk_delete_leads(
    body: LeadBulkUpdate, # Reuse schema for lead_ids list
    current_user: User = Depends(require_crm_delete),
    db: AsyncSession = Depends(get_db),
):
    query = select(Lead).where(Lead.id.in_(body.lead_ids), Lead.organization_id == current_user.organization_id)
    result = await db.execute(query)
    leads = result.scalars().all()
    for lead in leads:
        await db.delete(lead)
    await db.commit()
    return {"deleted": len(leads)}

@router.post("/{lead_id}/merge", response_model=Dict[str, Any])
async def merge_leads(
    lead_id: str,
    body: LeadMergeRequest,
    current_user: User = Depends(require_crm_write),
    db: AsyncSession = Depends(get_db),
):
    target_lead = await db.get(Lead, lead_id)
    source_lead = await db.get(Lead, body.source_lead_id)
    
    if not target_lead or target_lead.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Target lead not found")
    if not source_lead or source_lead.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Source lead not found")

    target_lead.phone = target_lead.phone or source_lead.phone
    target_lead.email = target_lead.email or source_lead.email
    target_lead.company = target_lead.company or source_lead.company
    target_lead.value = max(float(target_lead.value or 0), float(source_lead.value or 0))

    await db.delete(source_lead)
    
    history = LeadHistory(
        lead_id=target_lead.id,
        actor_id=current_user.id,
        action="merge",
        old_value=body.source_lead_id,
        new_value=target_lead.id
    )
    db.add(history)
    
    await db.commit()
    return _serialize(target_lead)

@router.get("/{lead_id}/notes", response_model=List[LeadNoteResponse])
async def get_lead_notes(lead_id: str, current_user: User = Depends(require_crm_read), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LeadNote).where(LeadNote.lead_id == lead_id).order_by(LeadNote.created_at.desc()))
    return result.scalars().all()

@router.post("/{lead_id}/notes", response_model=LeadNoteResponse)
async def create_lead_note(lead_id: str, body: LeadNoteCreate, current_user: User = Depends(require_crm_write), db: AsyncSession = Depends(get_db)):
    lead = await db.get(Lead, lead_id)
    if not lead or lead.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Lead not found")
    note = LeadNote(lead_id=lead_id, author_id=current_user.id, content=body.content)
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note

@router.get("/{lead_id}/tags", response_model=List[TagResponse])
async def get_lead_tags(lead_id: str, current_user: User = Depends(require_crm_read), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Tag).join(LeadTag, LeadTag.tag_id == Tag.id).where(LeadTag.lead_id == lead_id)
    )
    return result.scalars().all()

@router.post("/{lead_id}/tags", response_model=Dict[str, Any])
async def add_lead_tag(lead_id: str, body: TagCreate, current_user: User = Depends(require_crm_write), db: AsyncSession = Depends(get_db)):
    lead = await db.get(Lead, lead_id)
    if not lead or lead.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    result = await db.execute(select(Tag).where(Tag.name == body.name, Tag.organization_id == current_user.organization_id))
    tag = result.scalar_one_or_none()
    if not tag:
        tag = Tag(organization_id=current_user.organization_id, name=body.name.strip(), color=body.color)
        db.add(tag)
        await db.commit()
        await db.refresh(tag)
        
    lead_tag = LeadTag(lead_id=lead_id, tag_id=tag.id)
    db.add(lead_tag)
    await db.commit()
    return {"success": True, "tag": {"id": tag.id, "name": tag.name, "color": tag.color}}
