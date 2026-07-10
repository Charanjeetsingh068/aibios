import os

file_path = "backend/app/schemas/leads.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace VALID_STATUSES
content = content.replace(
    'VALID_STATUSES = {"new", "qualified", "pending", "spam", "assigned", "closed"}',
    'VALID_STATUSES = {"new", "contacted", "qualified", "proposal sent", "negotiation", "won", "lost", "spam", "duplicate", "archived"}'
)

new_schemas = """
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
"""

content += new_schemas

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Schemas patched")
