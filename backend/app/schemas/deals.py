from typing import Optional
from pydantic import BaseModel, Field

VALID_STAGES = {"lead", "qualified", "meeting", "proposal", "negotiation", "won", "lost"}


class DealCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    company: Optional[str] = Field(None, max_length=150)
    value: float = 0
    stage: str = Field("lead", max_length=20)
    lead_id: Optional[str] = None


class DealUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    value: Optional[float] = None
    stage: Optional[str] = None
    assigned_to: Optional[str] = None
