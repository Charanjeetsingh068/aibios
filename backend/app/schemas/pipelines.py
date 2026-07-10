from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class PipelineStageCreate(BaseModel):
    name: str = Field(..., max_length=100)
    order_index: int = 0

class PipelineStageUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    order_index: Optional[int] = None

class PipelineStageResponse(BaseModel):
    id: str
    pipeline_id: str
    name: str
    order_index: int
    created_at: datetime
    class Config:
        from_attributes = True

class PipelineCreate(BaseModel):
    name: str = Field(..., max_length=100)
    is_default: bool = False

class PipelineUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    is_default: Optional[bool] = None

class PipelineResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    is_default: bool
    created_at: datetime
    stages: List[PipelineStageResponse] = []
    class Config:
        from_attributes = True
