import asyncio
import logging
import time
import platform
import os
from datetime import datetime, date, time as dt_time, timedelta
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db, verify_postgres, verify_mongo, verify_redis, verify_qdrant
from app.core import telemetry
from app.api.v1.endpoints.auth import get_current_user
from app.api.v1.endpoints.system import get_uptime
from app.models.auth import User, Organization, Role, Permission
from app.models.business import (
    Lead, Deal, Campaign, CallLog, Meeting, TaskItem, EmailQueueItem, TokenUsageEvent,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/metrics", response_model=Dict[str, Any])
async def get_dashboard_metrics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns aggregated business and system metrics for the enterprise dashboard."""
    # Real DB counts
    total_orgs_result = await db.execute(select(func.count(Organization.id)))
    total_orgs = total_orgs_result.scalar() or 0

    total_users_result = await db.execute(select(func.count(User.id)))
    total_users = total_users_result.scalar() or 0

    active_users_result = await db.execute(
        select(func.count(User.id)).where(User.status == "active")
    )
    active_users = active_users_result.scalar() or 0

    suspended_users_result = await db.execute(
        select(func.count(User.id)).where(User.status == "suspended")
    )
    suspended_users = suspended_users_result.scalar() or 0

    total_roles_result = await db.execute(select(func.count(Role.id)))
    total_roles = total_roles_result.scalar() or 0

    stats = telemetry.get_stats()

    return {
        "total_organizations": total_orgs,
        "total_users": total_users,
        "online_users": active_users,
        "suspended_users": suspended_users,
        "total_roles": total_roles,
        "server_health": "healthy",
        "api_requests_today": stats["requests_today"],
        "avg_response_time_ms": stats["avg_response_time_ms"],
        "platform": platform.system(),
        "cpu_count": os.cpu_count() or 1,
        "python_version": platform.python_version(),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/overview", response_model=Dict[str, Any])
async def get_dashboard_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns the fully backend-driven summary powering the main Dashboard page."""
    org_id = current_user.organization_id
    today_start = datetime.combine(date.today(), dt_time.min)
    tomorrow_start = today_start + timedelta(days=1)

    async def count(stmt) -> int:
        result = await db.execute(stmt)
        return result.scalar() or 0

    total_orgs = await count(select(func.count(Organization.id)))
    total_users = await count(select(func.count(User.id)))
    online_users = await count(select(func.count(User.id)).where(User.status == "active"))

    today_leads = await count(
        select(func.count(Lead.id)).where(Lead.organization_id == org_id, Lead.created_at >= today_start)
    )
    qualified_leads = await count(
        select(func.count(Lead.id)).where(
            Lead.organization_id == org_id, Lead.created_at >= today_start, Lead.status == "qualified"
        )
    )
    spam_leads = await count(
        select(func.count(Lead.id)).where(
            Lead.organization_id == org_id, Lead.created_at >= today_start, Lead.status == "spam"
        )
    )
    facebook_leads = await count(
        select(func.count(Lead.id)).where(
            Lead.organization_id == org_id, Lead.created_at >= today_start, Lead.source == "facebook"
        )
    )
    instagram_leads = await count(
        select(func.count(Lead.id)).where(
            Lead.organization_id == org_id, Lead.created_at >= today_start, Lead.source == "instagram"
        )
    )
    whatsapp_leads = await count(
        select(func.count(Lead.id)).where(
            Lead.organization_id == org_id, Lead.created_at >= today_start, Lead.source == "whatsapp"
        )
    )

    today_calls = await count(
        select(func.count(CallLog.id)).where(CallLog.organization_id == org_id, CallLog.created_at >= today_start)
    )
    today_meetings = await count(
        select(func.count(Meeting.id)).where(
            Meeting.organization_id == org_id,
            Meeting.scheduled_at >= today_start,
            Meeting.scheduled_at < tomorrow_start,
        )
    )
    today_tasks = await count(
        select(func.count(TaskItem.id)).where(TaskItem.organization_id == org_id, TaskItem.completed.is_(False))
    )

    open_deals = await count(
        select(func.count(Deal.id)).where(Deal.organization_id == org_id, Deal.stage.notin_(["won", "lost"]))
    )
    won_deals = await count(
        select(func.count(Deal.id)).where(Deal.organization_id == org_id, Deal.stage == "won")
    )
    revenue_result = await db.execute(
        select(func.coalesce(func.sum(Deal.value), 0)).where(Deal.organization_id == org_id, Deal.stage == "won")
    )
    revenue = float(revenue_result.scalar() or 0)

    campaigns_running = await count(
        select(func.count(Campaign.id)).where(Campaign.organization_id == org_id, Campaign.status == "running")
    )
    email_queue = await count(
        select(func.count(EmailQueueItem.id)).where(
            EmailQueueItem.organization_id == org_id, EmailQueueItem.status == "pending"
        )
    )

    token_result = await db.execute(
        select(
            func.coalesce(func.sum(TokenUsageEvent.input_tokens), 0),
            func.coalesce(func.sum(TokenUsageEvent.output_tokens), 0),
        ).where(TokenUsageEvent.organization_id == org_id)
    )
    token_row = token_result.first()
    input_tokens = int(token_row[0] or 0) if token_row else 0
    output_tokens = int(token_row[1] or 0) if token_row else 0

    postgres_ok, mongo_ok, redis_ok, qdrant_ok = await asyncio.gather(
        verify_postgres(), verify_mongo(), verify_redis(), verify_qdrant()
    )
    server_health = "healthy" if all([postgres_ok, mongo_ok, redis_ok, qdrant_ok]) else "degraded"

    stats = telemetry.get_stats()

    return {
        "backendStatus": "online",
        "uptime": get_uptime(),
        "organizations": total_orgs,
        "users": total_users,
        "onlineUsers": online_users,
        "todayLeads": today_leads,
        "qualifiedLeads": qualified_leads,
        "spamLeads": spam_leads,
        "todayCalls": today_calls,
        "todayMeetings": today_meetings,
        "todayTasks": today_tasks,
        "openDeals": open_deals,
        "wonDeals": won_deals,
        "revenue": revenue,
        "campaignsRunning": campaigns_running,
        "facebookLeads": facebook_leads,
        "instagramLeads": instagram_leads,
        "whatsappLeads": whatsapp_leads,
        "emailQueue": email_queue,
        "serverHealth": server_health,
        "apiRequests": stats["requests_today"],
        "responseTime": stats["avg_response_time_ms"],
        "tokenUsage": input_tokens + output_tokens,
        "tokenUsageInput": input_tokens,
        "tokenUsageOutput": output_tokens,
        "timestamp": datetime.utcnow().isoformat(),
    }


class TaskCreateBody(BaseModel):
    text: str


@router.get("/tasks", response_model=Dict[str, Any])
async def list_tasks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns open/recent tasks for the organization."""
    query = (
        select(TaskItem)
        .where(TaskItem.organization_id == current_user.organization_id)
        .order_by(TaskItem.created_at.desc())
        .limit(50)
    )
    result = await db.execute(query)
    items = result.scalars().all()
    return {
        "tasks": [
            {"id": t.id, "text": t.text, "completed": t.completed, "created_at": t.created_at.isoformat() if t.created_at else None}
            for t in items
        ]
    }


@router.post("/tasks", response_model=Dict[str, Any])
async def create_task(
    body: TaskCreateBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    task = TaskItem(organization_id=current_user.organization_id, text=body.text.strip(), completed=False)
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return {"id": task.id, "text": task.text, "completed": task.completed, "created_at": task.created_at.isoformat()}


@router.patch("/tasks/{task_id}", response_model=Dict[str, Any])
async def toggle_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    task = await db.get(TaskItem, task_id)
    if not task or task.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Task not found")
    task.completed = not task.completed
    await db.commit()
    return {"id": task.id, "completed": task.completed}


@router.delete("/tasks/{task_id}", response_model=Dict[str, Any])
async def delete_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    task = await db.get(TaskItem, task_id)
    if not task or task.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Task not found")
    await db.delete(task)
    await db.commit()
    return {"success": True}


@router.get("/campaigns", response_model=Dict[str, Any])
async def list_campaigns(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(Campaign)
        .where(Campaign.organization_id == current_user.organization_id)
        .order_by(Campaign.created_at.desc())
    )
    result = await db.execute(query)
    items = result.scalars().all()
    return {
        "campaigns": [
            {"id": c.id, "name": c.name, "channel": c.channel, "status": c.status, "progress": c.progress}
            for c in items
        ]
    }


class CampaignCreateBody(BaseModel):
    name: str
    channel: str = "general"


@router.post("/campaigns", response_model=Dict[str, Any])
async def create_campaign(
    body: CampaignCreateBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    campaign = Campaign(
        organization_id=current_user.organization_id,
        name=body.name.strip(),
        channel=body.channel,
        status="paused",
        progress=0,
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    return {"id": campaign.id, "name": campaign.name, "channel": campaign.channel, "status": campaign.status, "progress": campaign.progress}


@router.patch("/campaigns/{campaign_id}/toggle", response_model=Dict[str, Any])
async def toggle_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    campaign = await db.get(Campaign, campaign_id)
    if not campaign or campaign.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Campaign not found")
    campaign.status = "paused" if campaign.status == "running" else "running"
    await db.commit()
    return {"id": campaign.id, "status": campaign.status}


@router.delete("/campaigns/{campaign_id}", response_model=Dict[str, Any])
async def delete_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    campaign = await db.get(Campaign, campaign_id)
    if not campaign or campaign.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Campaign not found")
    await db.delete(campaign)
    await db.commit()
    return {"success": True}


@router.get("/meetings", response_model=Dict[str, Any])
async def list_meetings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(Meeting)
        .where(Meeting.organization_id == current_user.organization_id)
        .order_by(Meeting.scheduled_at.asc())
        .limit(20)
    )
    result = await db.execute(query)
    items = result.scalars().all()
    return {
        "meetings": [
            {"id": m.id, "title": m.title, "scheduled_at": m.scheduled_at.isoformat() if m.scheduled_at else None}
            for m in items
        ]
    }


class MeetingCreateBody(BaseModel):
    title: str
    scheduled_at: datetime


@router.post("/meetings", response_model=Dict[str, Any])
async def create_meeting(
    body: MeetingCreateBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    meeting = Meeting(
        organization_id=current_user.organization_id,
        title=body.title.strip(),
        scheduled_at=body.scheduled_at,
    )
    db.add(meeting)
    await db.commit()
    await db.refresh(meeting)
    return {"id": meeting.id, "title": meeting.title, "scheduled_at": meeting.scheduled_at.isoformat()}


@router.delete("/meetings/{meeting_id}", response_model=Dict[str, Any])
async def delete_meeting(
    meeting_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    meeting = await db.get(Meeting, meeting_id)
    if not meeting or meeting.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Meeting not found")
    await db.delete(meeting)
    await db.commit()
    return {"success": True}


@router.get("/users", response_model=Dict[str, Any])
async def get_users_list(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns paginated list of users in the same organization."""
    query = (
        select(User)
        .where(User.organization_id == current_user.organization_id)
        .options(selectinload(User.role))
        .order_by(User.created_at.desc())
        .limit(200)
    )
    result = await db.execute(query)
    users = result.scalars().all()

    return {
        "users": [
            {
                "id": u.id,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "email": u.email,
                "phone": u.phone,
                "status": u.status,
                "role_id": u.role_id,
                "role_name": u.role.name if u.role else u.role_id,
                "permissions": [p.id for p in u.role.permissions] if u.role else [],
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "last_login": u.last_login.isoformat() if u.last_login else None,
            }
            for u in users
        ],
        "total": len(users),
    }


class UserInviteBody(BaseModel):
    name: str
    email: str
    role: str
    permissions: List[str] = []


@router.post("/users/invite", response_model=Dict[str, Any])
async def invite_user(
    body: UserInviteBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from app.core.security import get_password_hash
    import secrets

    name_parts = body.name.strip().split(" ", 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ""

    # Check if user already exists
    existing = await db.execute(select(User).where(User.email == body.email.strip()))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User with this email already exists")

    # Add user
    new_u = User(
        organization_id=current_user.organization_id,
        first_name=first_name,
        last_name=last_name,
        email=body.email.strip(),
        password_hash=get_password_hash("123456"),
        status="invited",
        role_id=body.role
    )
    db.add(new_u)
    await db.commit()
    await db.refresh(new_u)

    invite_token = secrets.token_urlsafe(16)
    invite_link = f"http://localhost:3000/auth/login?invite={invite_token}"

    return {
        "user": {
            "id": new_u.id,
            "first_name": new_u.first_name,
            "last_name": new_u.last_name,
            "email": new_u.email,
            "status": new_u.status,
            "role_id": new_u.role_id,
        },
        "invite_link": invite_link
    }


class UserUpdateBody(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None


@router.patch("/users/{user_id}", response_model=Dict[str, Any])
async def update_user_details(
    user_id: str,
    body: UserUpdateBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    u = await db.get(User, user_id)
    if not u or u.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="User not found")

    if body.name is not None:
        name_parts = body.name.strip().split(" ", 1)
        u.first_name = name_parts[0]
        u.last_name = name_parts[1] if len(name_parts) > 1 else ""
    if body.email is not None:
        u.email = body.email.strip()
    if body.role is not None:
        u.role_id = body.role
    if body.status is not None:
        u.status = body.status

    await db.commit()
    await db.refresh(u)
    return {
        "id": u.id,
        "first_name": u.first_name,
        "last_name": u.last_name,
        "email": u.email,
        "status": u.status,
        "role_id": u.role_id
    }


@router.delete("/users/{user_id}", response_model=Dict[str, Any])
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    u = await db.get(User, user_id)
    if not u or u.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(u)
    await db.commit()
    return {"success": True}


@router.post("/users/{user_id}/reset-password", response_model=Dict[str, Any])
async def reset_user_password(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    u = await db.get(User, user_id)
    if not u or u.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="User not found")

    import secrets
    token = secrets.token_urlsafe(16)
    reset_link = f"http://localhost:3000/auth/reset-password?token={token}"
    return {"reset_link": reset_link}


class RoleUpdateBody(BaseModel):
    permissions: List[str]


@router.patch("/roles/{role_id}", response_model=Dict[str, Any])
async def update_role_permissions(
    role_id: str,
    body: RoleUpdateBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    role.permissions.clear()

    for p_id in body.permissions:
        perm = await db.get(Permission, p_id)
        if perm:
            role.permissions.append(perm)

    await db.commit()
    await db.refresh(role)
    return {
        "id": role.id,
        "name": role.name,
        "permissions": [{"id": p.id, "name": p.name} for p in role.permissions]
    }


@router.get("/roles", response_model=Dict[str, Any])
async def get_roles_list(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns all configured RBAC roles with their permissions."""
    query = select(Role).options(selectinload(Role.permissions))
    result = await db.execute(query)
    roles = result.scalars().all()

    return {
        "roles": [
            {
                "id": r.id,
                "name": r.name,
                "description": r.description,
                "permissions": [{"id": p.id, "name": p.name} for p in r.permissions],
                "permissions_count": len(r.permissions),
            }
            for r in roles
        ],
        "total": len(roles),
    }


@router.get("/organization", response_model=Dict[str, Any])
async def get_organization_details(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns current user's organization details."""
    query = (
        select(Organization)
        .where(Organization.id == current_user.organization_id)
    )
    result = await db.execute(query)
    org = result.scalar_one_or_none()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    user_count_result = await db.execute(
        select(func.count(User.id)).where(User.organization_id == org.id)
    )
    user_count = user_count_result.scalar() or 0

    return {
        "id": org.id,
        "name": org.name,
        "slug": org.slug,
        "status": org.status,
        "logo_char": org.logo_char,
        "gst_number": org.gst_number,
        "address": org.address,
        "timezone": org.timezone,
        "brand_color": org.brand_color,
        "subscription_plan": org.subscription_plan,
        "smtp_host": org.smtp_host,
        "smtp_port": org.smtp_port,
        "smtp_user": org.smtp_user,
        "smtp_pass": org.smtp_pass,
        "user_count": user_count,
        "created_at": org.created_at.isoformat() if org.created_at else None,
    }


class OrganizationUpdateBody(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    logo_char: Optional[str] = None
    gst_number: Optional[str] = None
    address: Optional[str] = None
    timezone: Optional[str] = None
    brand_color: Optional[str] = None
    subscription_plan: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_pass: Optional[str] = None


@router.patch("/organization", response_model=Dict[str, Any])
async def update_organization_details(
    body: OrganizationUpdateBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(Organization)
        .where(Organization.id == current_user.organization_id)
    )
    result = await db.execute(query)
    org = result.scalar_one_or_none()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    changes = body.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(org, field, value)

    await db.commit()
    await db.refresh(org)

    user_count_result = await db.execute(
        select(func.count(User.id)).where(User.organization_id == org.id)
    )
    user_count = user_count_result.scalar() or 0

    return {
        "id": org.id,
        "name": org.name,
        "slug": org.slug,
        "status": org.status,
        "logo_char": org.logo_char,
        "gst_number": org.gst_number,
        "address": org.address,
        "timezone": org.timezone,
        "brand_color": org.brand_color,
        "subscription_plan": org.subscription_plan,
        "smtp_host": org.smtp_host,
        "smtp_port": org.smtp_port,
        "smtp_user": org.smtp_user,
        "smtp_pass": org.smtp_pass,
        "user_count": user_count,
        "created_at": org.created_at.isoformat() if org.created_at else None,
    }


@router.get("/audit-logs", response_model=Dict[str, Any])
async def get_audit_logs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns recent audit log entries for the organization."""
    from app.models.auth import AuditLog
    query = (
        select(AuditLog)
        .where(AuditLog.organization_id == current_user.organization_id)
        .order_by(AuditLog.created_at.desc())
        .limit(100)
    )
    result = await db.execute(query)
    logs = result.scalars().all()

    return {
        "logs": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "description": log.description,
                "resource": log.resource,
                "resource_id": log.resource_id,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
        "total": len(logs),
    }
