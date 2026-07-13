import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user, PermissionChecker
from app.models.auth import User, Team, TeamMember, AuditLog
from app.schemas.teams import TeamCreate, TeamUpdate, TeamResponse, TeamMemberBase, TeamMemberResponse

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=TeamResponse)
async def create_team(
    team_data: TeamCreate,
    current_user: User = Depends(PermissionChecker("users.write")),
    db: AsyncSession = Depends(get_db)
):
    team = Team(
        organization_id=current_user.organization_id,
        name=team_data.name,
        manager_id=team_data.manager_id
    )
    db.add(team)
    
    audit = AuditLog(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        action="team_create",
        description=f"Created team {team.name}",
        resource="teams",
        resource_id=team.id
    )
    db.add(audit)
    
    await db.commit()
    await db.refresh(team)
    return team

@router.get("/", response_model=List[TeamResponse])
async def list_teams(
    current_user: User = Depends(PermissionChecker("users.read")),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Team).where(Team.organization_id == current_user.organization_id))
    return result.scalars().all()

@router.patch("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: str,
    team_data: TeamUpdate,
    current_user: User = Depends(PermissionChecker("users.write")),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Team).where(Team.id == team_id, Team.organization_id == current_user.organization_id))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
        
    for k, v in team_data.model_dump(exclude_unset=True).items():
        setattr(team, k, v)
        
    audit = AuditLog(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        action="team_update",
        description=f"Updated team {team.name}",
        resource="teams",
        resource_id=team.id
    )
    db.add(audit)
    
    await db.commit()
    await db.refresh(team)
    return team

@router.post("/{team_id}/members", response_model=TeamMemberResponse)
async def add_team_member(
    team_id: str,
    member_data: TeamMemberBase,
    current_user: User = Depends(PermissionChecker("users.write")),
    db: AsyncSession = Depends(get_db)
):
    team_result = await db.execute(select(Team).where(Team.id == team_id, Team.organization_id == current_user.organization_id))
    if not team_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Team not found")
        
    # Check user is in same org
    user_result = await db.execute(select(User).where(User.id == member_data.user_id, User.organization_id == current_user.organization_id))
    if not user_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="User not found in organization")
        
    member = TeamMember(
        team_id=team_id,
        user_id=member_data.user_id,
        role=member_data.role
    )
    db.add(member)
    
    audit = AuditLog(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        action="team_member_add",
        description=f"Added user {member_data.user_id} to team",
        resource="teams",
        resource_id=team_id
    )
    db.add(audit)
    
    await db.commit()
    await db.refresh(member)
    return member
