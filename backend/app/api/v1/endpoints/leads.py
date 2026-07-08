import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, mongo_db
from app.core.realtime import emit_to_organization
from app.api.v1.endpoints.auth import get_current_user
from app.models.auth import User
from app.models.business import Lead
from app.schemas.leads import LeadCreate, LeadUpdate, LeadEventCreate, VALID_SOURCES, VALID_STATUSES

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
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
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
    )
    db.add(lead)
    await db.commit()
    await db.refresh(lead)

    await _record_mongo_lead(lead)
    await _record_lead_event(lead.id, lead.organization_id, "created", f"Lead created via {lead.source}", current_user.id)

    payload = _serialize(lead)
    await emit_to_organization(lead.organization_id, "lead:new", payload)
    return payload


@router.get("/{lead_id}", response_model=Dict[str, Any])
async def get_lead(
    lead_id: str,
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    lead = await db.get(Lead, lead_id)
    if not lead or lead.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Lead not found")

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
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    lead = await db.get(Lead, lead_id)
    if not lead or lead.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Lead not found")

    await _record_lead_event(lead_id, lead.organization_id, body.type, body.note, current_user.id)
    return {"success": True}
