import logging
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.realtime import emit_to_organization
from app.api.v1.endpoints.auth import get_current_user
from app.models.auth import User
from app.models.business import Deal
from app.schemas.deals import DealCreate, DealUpdate, VALID_STAGES

logger = logging.getLogger(__name__)
router = APIRouter()


def _serialize(deal: Deal) -> Dict[str, Any]:
    return {
        "id": deal.id,
        "organization_id": deal.organization_id,
        "lead_id": deal.lead_id,
        "name": deal.name,
        "company": deal.company,
        "stage": deal.stage,
        "value": float(deal.value or 0),
        "assigned_to": deal.assigned_to,
        "created_at": deal.created_at.isoformat() if deal.created_at else None,
        "updated_at": deal.updated_at.isoformat() if deal.updated_at else None,
    }


@router.get("", response_model=Dict[str, Any])
async def list_deals(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Deal)
        .where(Deal.organization_id == current_user.organization_id)
        .order_by(Deal.created_at.desc())
    )
    result = await db.execute(query)
    deals = result.scalars().all()
    return {"deals": [_serialize(d) for d in deals]}


@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_deal(
    body: DealCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.stage not in VALID_STAGES:
        raise HTTPException(status_code=400, detail=f"Invalid stage. Must be one of {sorted(VALID_STAGES)}")

    deal = Deal(
        organization_id=current_user.organization_id,
        lead_id=body.lead_id,
        name=body.name.strip(),
        company=body.company,
        value=body.value,
        stage=body.stage,
    )
    db.add(deal)
    await db.commit()
    await db.refresh(deal)

    payload = _serialize(deal)
    await emit_to_organization(deal.organization_id, "deal:new", payload)
    return payload


@router.patch("/{deal_id}", response_model=Dict[str, Any])
async def update_deal(
    deal_id: str,
    body: DealUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deal = await db.get(Deal, deal_id)
    if not deal or deal.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Deal not found")

    if body.stage is not None and body.stage not in VALID_STAGES:
        raise HTTPException(status_code=400, detail=f"Invalid stage. Must be one of {sorted(VALID_STAGES)}")

    changes = body.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(deal, field, value)

    await db.commit()
    await db.refresh(deal)

    payload = _serialize(deal)
    await emit_to_organization(deal.organization_id, "deal:updated", payload)
    return payload


@router.delete("/{deal_id}", response_model=Dict[str, Any])
async def delete_deal(
    deal_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deal = await db.get(Deal, deal_id)
    if not deal or deal.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Deal not found")

    await db.delete(deal)
    await db.commit()

    await emit_to_organization(current_user.organization_id, "deal:deleted", {"id": deal_id})
    return {"success": True}
