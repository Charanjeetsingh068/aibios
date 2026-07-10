from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import PermissionChecker
from app.core.database import get_db
from app.models.auth import User
from app.models.business import Pipeline, PipelineStage
from app.schemas.pipelines import (
    PipelineCreate,
    PipelineResponse,
    PipelineStageCreate,
    PipelineStageResponse,
    PipelineUpdate,
)

router = APIRouter()
require_crm_read = PermissionChecker("crm.read")
require_crm_write = PermissionChecker("crm.write")

def _serialize_pipeline(pipeline: Pipeline, stages: List[PipelineStage] = []) -> Dict[str, Any]:
    return {
        "id": pipeline.id,
        "organization_id": pipeline.organization_id,
        "name": pipeline.name,
        "is_default": pipeline.is_default,
        "created_at": pipeline.created_at,
        "stages": [
            {
                "id": s.id,
                "pipeline_id": s.pipeline_id,
                "name": s.name,
                "order_index": s.order_index,
                "created_at": s.created_at
            } for s in sorted(stages, key=lambda x: x.order_index)
        ]
    }

@router.get("", response_model=List[PipelineResponse])
async def list_pipelines(current_user: User = Depends(require_crm_read), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Pipeline).where(Pipeline.organization_id == current_user.organization_id))
    pipelines = result.scalars().all()
    
    stage_result = await db.execute(select(PipelineStage).where(PipelineStage.pipeline_id.in_([p.id for p in pipelines])))
    stages = stage_result.scalars().all()
    stages_by_pipeline = {p.id: [] for p in pipelines}
    for s in stages:
        if s.pipeline_id in stages_by_pipeline:
            stages_by_pipeline[s.pipeline_id].append(s)

    return [_serialize_pipeline(p, stages_by_pipeline[p.id]) for p in pipelines]

@router.post("", response_model=PipelineResponse, status_code=status.HTTP_201_CREATED)
async def create_pipeline(body: PipelineCreate, current_user: User = Depends(require_crm_write), db: AsyncSession = Depends(get_db)):
    if body.is_default:
        await db.execute(
            Pipeline.__table__.update()
            .where(Pipeline.organization_id == current_user.organization_id)
            .values(is_default=False)
        )
    
    pipeline = Pipeline(
        organization_id=current_user.organization_id,
        name=body.name.strip(),
        is_default=body.is_default
    )
    db.add(pipeline)
    await db.commit()
    await db.refresh(pipeline)
    return _serialize_pipeline(pipeline, [])

@router.patch("/{pipeline_id}", response_model=PipelineResponse)
async def update_pipeline(pipeline_id: str, body: PipelineUpdate, current_user: User = Depends(require_crm_write), db: AsyncSession = Depends(get_db)):
    pipeline = await db.get(Pipeline, pipeline_id)
    if not pipeline or pipeline.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    if body.is_default:
        await db.execute(
            Pipeline.__table__.update()
            .where(Pipeline.organization_id == current_user.organization_id)
            .values(is_default=False)
        )
        pipeline.is_default = True

    if body.name is not None:
        pipeline.name = body.name.strip()

    await db.commit()
    await db.refresh(pipeline)
    
    stage_result = await db.execute(select(PipelineStage).where(PipelineStage.pipeline_id == pipeline_id))
    stages = stage_result.scalars().all()
    return _serialize_pipeline(pipeline, stages)

@router.delete("/{pipeline_id}")
async def delete_pipeline(pipeline_id: str, current_user: User = Depends(require_crm_write), db: AsyncSession = Depends(get_db)):
    pipeline = await db.get(Pipeline, pipeline_id)
    if not pipeline or pipeline.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    if pipeline.is_default:
        raise HTTPException(status_code=400, detail="Cannot delete default pipeline")
    
    await db.delete(pipeline)
    await db.commit()
    return {"success": True}

@router.post("/{pipeline_id}/stages", response_model=PipelineStageResponse)
async def create_stage(pipeline_id: str, body: PipelineStageCreate, current_user: User = Depends(require_crm_write), db: AsyncSession = Depends(get_db)):
    pipeline = await db.get(Pipeline, pipeline_id)
    if not pipeline or pipeline.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    stage = PipelineStage(
        pipeline_id=pipeline_id,
        name=body.name.strip(),
        order_index=body.order_index
    )
    db.add(stage)
    await db.commit()
    await db.refresh(stage)
    return stage

@router.delete("/stages/{stage_id}")
async def delete_stage(stage_id: str, current_user: User = Depends(require_crm_write), db: AsyncSession = Depends(get_db)):
    stage = await db.get(PipelineStage, stage_id)
    if not stage:
        raise HTTPException(status_code=404, detail="Stage not found")
    
    pipeline = await db.get(Pipeline, stage.pipeline_id)
    if not pipeline or pipeline.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    await db.delete(stage)
    await db.commit()
    return {"success": True}
