from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

VALID_SOURCES = {"website", "manual", "facebook", "instagram", "whatsapp", "ai_voice"}
VALID_STATUSES = {"new", "contacted", "qualified", "proposal sent", "negotiation", "won", "lost", "spam", "duplicate", "archived"}


class LeadCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    company: Optional[str] = Field(None, max_length=150)
    phone: Optional[str] = Field(None, max_length=30)
    email: Optional[str] = Field(None, max_length=255)
    source: str = Field("manual", max_length=30)
    value: float = 0
    campaign_id: Optional[str] = None


class LeadUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    company: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    status: Optional[str] = None
    value: Optional[float] = None
    campaign_id: Optional[str] = None
    assigned_to: Optional[str] = None


class LeadEventCreate(BaseModel):
    type: str = Field(..., max_length=50)
    note: str = Field(..., max_length=2000)


class LeadResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    company: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    source: str
    status: str
    value: float
    campaign_id: Optional[str] = None
    assigned_to: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

from typing import List


class LeadNoteCreate(BaseModel):
    content: str = Field(..., max_length=2000)

class LeadNoteResponse(BaseModel):
    id: str
    lead_id: str
    author_id: Optional[str]
    content: str
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class LeadTaskCreate(BaseModel):
    text: str = Field(..., max_length=500)
    assigned_to: Optional[str] = None

class LeadMeetingCreate(BaseModel):
    title: str = Field(..., max_length=200)
    scheduled_at: datetime

class TagCreate(BaseModel):
    name: str = Field(..., max_length=50)
    color: str = Field("#CCCCCC", max_length=20)

class TagResponse(BaseModel):
    id: str
    name: str
    color: str
    class Config:
        from_attributes = True

class LeadBulkUpdate(BaseModel):
    lead_ids: List[str]
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    campaign_id: Optional[str] = None

class LeadMergeRequest(BaseModel):
    source_lead_id: str
    target_lead_id: str
