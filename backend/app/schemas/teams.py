from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

class TeamBase(BaseModel):
    name: str = Field(..., max_length=100)
    manager_id: Optional[str] = None

class TeamCreate(TeamBase):
    pass

class TeamUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    manager_id: Optional[str] = None

class TeamResponse(TeamBase):
    id: str
    organization_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TeamMemberBase(BaseModel):
    user_id: str
    role: str = "member"

class TeamMemberResponse(TeamMemberBase):
    team_id: str
    joined_at: datetime

    class Config:
        from_attributes = True
