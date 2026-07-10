import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_user
from app.core.database import get_db
from app.models.auth import User
from app.models.business import Workflow

logger = logging.getLogger(__name__)
router = APIRouter()


def _serialize(wf: Workflow) -> Dict[str, Any]:
    return {
        "id": wf.id,
        "name": wf.name,
        "trigger": wf.trigger,
        "status": wf.status,
        "runs": wf.runs,
        "created_at": wf.created_at.isoformat() if wf.created_at else None,
    }


@router.get("", response_model=Dict[str, Any])
async def list_workflows(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Workflow)
        .where(Workflow.organization_id == current_user.organization_id)
        .order_by(Workflow.created_at.desc())
    )
    res = await db.execute(query)
    items = res.scalars().all()
    return {"workflows": [_serialize(w) for w in items]}


class WorkflowCreateBody(BaseModel):
    name: str
    trigger: str
    status: Optional[str] = "active"


@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_workflow(
    body: WorkflowCreateBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    wf = Workflow(
        organization_id=current_user.organization_id,
        name=body.name.strip(),
        trigger=body.trigger.strip(),
        status=body.status,
        runs=0,
    )
    db.add(wf)
    await db.commit()
    await db.refresh(wf)
    return _serialize(wf)


class WorkflowUpdateBody(BaseModel):
    name: Optional[str] = None
    trigger: Optional[str] = None
    status: Optional[str] = None


@router.patch("/{wf_id}", response_model=Dict[str, Any])
async def update_workflow(
    wf_id: str,
    body: WorkflowUpdateBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    wf = await db.get(Workflow, wf_id)
    if not wf or wf.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Workflow not found")

    changes = body.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(wf, field, value)

    await db.commit()
    await db.refresh(wf)
    return _serialize(wf)


@router.delete("/{wf_id}", response_model=Dict[str, Any])
async def delete_workflow(
    wf_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    wf = await db.get(Workflow, wf_id)
    if not wf or wf.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Workflow not found")

    await db.delete(wf)
    await db.commit()
    return {"success": True}


@router.post("/{wf_id}/run", response_model=Dict[str, Any])
async def run_workflow(
    wf_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    wf = await db.get(Workflow, wf_id)
    if not wf or wf.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Workflow not found")

    wf.runs += 1
    await db.commit()
    return {"success": True, "runs": wf.runs}


@router.get("/{wf_id}/history", response_model=Dict[str, Any])
async def workflow_history(
    wf_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    wf = await db.get(Workflow, wf_id)
    if not wf or wf.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # No per-run execution log is persisted yet (only the aggregate `runs` counter on the
    # workflow itself) — return a real empty history rather than fabricated run records.
    return {"history": []}
