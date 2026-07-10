import logging
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.endpoints.auth import PermissionChecker
from app.core.audit import record_audit_log
from app.core.config import settings
from app.core.database import get_db
from app.core.email import send_email
from app.core.pagination import PageParams, apply_sort, pagination_params
from app.core.security import get_password_hash
from app.models.auth import Organization, PasswordResetToken, Role, User

logger = logging.getLogger(__name__)
router = APIRouter()

require_users_read = PermissionChecker("users.read")
require_users_write = PermissionChecker("users.write")
require_users_delete = PermissionChecker("users.delete")
require_users_suspend = PermissionChecker("users.suspend")
require_users_invite = PermissionChecker("users.invite")
require_users_reset_password = PermissionChecker("users.reset_password")
require_users_assign_role = PermissionChecker("users.assign_role")

ALLOWED_SORT_COLUMNS = {"first_name", "last_name", "email", "status", "created_at", "last_login"}


def _is_platform_admin(user: User) -> bool:
    return "admin.all" in user.all_permission_ids()


def _check_org_scope(current_user: User, target_organization_id: str) -> None:
    if _is_platform_admin(current_user):
        return
    if current_user.organization_id != target_organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot manage users outside your organization")


def _serialize(user: User) -> Dict[str, Any]:
    return {
        "id": user.id,
        "organization_id": user.organization_id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "phone": user.phone,
        "status": user.status,
        "role_id": user.role_id,
        "roles": user.all_role_ids(),
        "department": user.department,
        "designation": user.designation,
        "profile_image": user.profile_image,
        "timezone": user.timezone,
        "language": user.language,
        "email_verified": user.email_verified,
        "mfa_enabled": user.mfa_enabled,
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "last_activity": user.last_activity.isoformat() if user.last_activity else None,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    }


@router.get("", response_model=Dict[str, Any])
async def list_users(
    current_user: User = Depends(require_users_read),
    db: AsyncSession = Depends(get_db),
    params: PageParams = Depends(pagination_params),
    organization_id: Optional[str] = None,
    status_filter: Optional[str] = None,
):
    query = select(User).options(selectinload(User.additional_roles)).where(User.deleted_at.is_(None))

    if _is_platform_admin(current_user):
        if organization_id:
            query = query.where(User.organization_id == organization_id)
    else:
        query = query.where(User.organization_id == current_user.organization_id)

    if status_filter:
        query = query.where(User.status == status_filter)
    if params.search:
        like = f"%{params.search}%"
        query = query.where(or_(User.first_name.ilike(like), User.last_name.ilike(like), User.email.ilike(like)))

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = apply_sort(query, User, params, ALLOWED_SORT_COLUMNS, "created_at")
    query = query.offset(params.skip).limit(params.limit)
    items = (await db.execute(query)).scalars().all()

    return {"users": [_serialize(u) for u in items], "total": total, "skip": params.skip, "limit": params.limit}


@router.get("/{user_id}", response_model=Dict[str, Any])
async def get_user(
    user_id: str,
    current_user: User = Depends(require_users_read),
    db: AsyncSession = Depends(get_db),
):
    query = select(User).options(selectinload(User.additional_roles)).where(User.id == user_id)
    user = (await db.execute(query)).scalar_one_or_none()
    if not user or user.deleted_at is not None:
        raise HTTPException(status_code=404, detail="User not found")
    _check_org_scope(current_user, user.organization_id)
    return _serialize(user)


class UserCreateBody(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str = Field(..., min_length=8)
    role_id: str
    organization_id: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    timezone: Optional[str] = "UTC"
    language: Optional[str] = "en"


async def _resolve_target_org(current_user: User, requested_org_id: Optional[str], db: AsyncSession) -> str:
    if _is_platform_admin(current_user):
        org_id = requested_org_id or current_user.organization_id
        org = await db.get(Organization, org_id)
        if not org or org.deleted_at is not None:
            raise HTTPException(status_code=404, detail="Organization not found")
        return org_id
    if requested_org_id and requested_org_id != current_user.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot create users outside your organization")
    return current_user.organization_id


async def _validate_role(role_id: str, db: AsyncSession) -> Role:
    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=400, detail=f"Unknown role '{role_id}'")
    return role


@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreateBody,
    request: Request,
    current_user: User = Depends(require_users_write),
    db: AsyncSession = Depends(get_db),
):
    existing = (await db.execute(select(User).where(User.email == body.email))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="A user with this email already exists")

    org_id = await _resolve_target_org(current_user, body.organization_id, db)
    await _validate_role(body.role_id, db)

    user = User(
        organization_id=org_id,
        first_name=body.first_name.strip(),
        last_name=body.last_name.strip(),
        email=body.email,
        phone=body.phone,
        password_hash=get_password_hash(body.password),
        role_id=body.role_id,
        department=body.department,
        designation=body.designation,
        timezone=body.timezone or "UTC",
        language=body.language or "en",
        status="active",
        created_by=current_user.id,
        updated_by=current_user.id,
    )
    db.add(user)
    await db.flush()
    await record_audit_log(
        db, actor=current_user, organization_id=org_id, action="user.create",
        description=f"User '{user.email}' created", resource="users", resource_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(user)
    return _serialize(user)


class UserInviteBody(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    role_id: str
    organization_id: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None


@router.post("/invite", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def invite_user(
    body: UserInviteBody,
    request: Request,
    current_user: User = Depends(require_users_invite),
    db: AsyncSession = Depends(get_db),
):
    existing = (await db.execute(select(User).where(User.email == body.email))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="A user with this email already exists")

    org_id = await _resolve_target_org(current_user, body.organization_id, db)
    await _validate_role(body.role_id, db)

    # Unusable placeholder password — the invited user sets a real one via the reset-password
    # link, which also flips status "invited" -> "active" (see auth.py reset_password).
    placeholder_password = secrets.token_urlsafe(32)
    user = User(
        organization_id=org_id,
        first_name=body.first_name.strip(),
        last_name=body.last_name.strip(),
        email=body.email,
        password_hash=get_password_hash(placeholder_password),
        role_id=body.role_id,
        department=body.department,
        designation=body.designation,
        status="invited",
        created_by=current_user.id,
        updated_by=current_user.id,
    )
    db.add(user)
    await db.flush()

    raw_token = secrets.token_urlsafe(32)
    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=get_password_hash(raw_token),
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db.add(reset_token)

    await record_audit_log(
        db, actor=current_user, organization_id=org_id, action="user.invite",
        description=f"User '{user.email}' invited", resource="users", resource_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(user)

    invite_link = f"{settings.FRONTEND_URL}/auth/reset-password?token={raw_token}"
    email_sent = await send_email(
        to=user.email,
        subject="You've been invited to AI-BOS",
        body=f"You've been invited to join AI-BOS. Set your password to get started:\n\n{invite_link}",
    )
    response = _serialize(user)
    if not email_sent:
        logger.warning(f"Invite email could not be sent to {user.email}; SMTP may not be configured.")
        if settings.ENVIRONMENT == "development":
            response["invite_link_dev_only"] = invite_link
    return response


class UserUpdateBody(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    profile_image: Optional[str] = None
    role_id: Optional[str] = None


@router.patch("/{user_id}", response_model=Dict[str, Any])
async def update_user(
    user_id: str,
    body: UserUpdateBody,
    request: Request,
    current_user: User = Depends(require_users_write),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, user_id)
    if not user or user.deleted_at is not None:
        raise HTTPException(status_code=404, detail="User not found")
    _check_org_scope(current_user, user.organization_id)

    changes = body.model_dump(exclude_unset=True)
    if "role_id" in changes:
        await _validate_role(changes["role_id"], db)
    for field, value in changes.items():
        setattr(user, field, value)
    user.updated_by = current_user.id

    await record_audit_log(
        db, actor=current_user, organization_id=user.organization_id, action="user.update",
        description=f"User '{user.email}' updated ({', '.join(changes.keys()) or 'no fields'})",
        resource="users", resource_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(user)
    return _serialize(user)


@router.post("/{user_id}/suspend", response_model=Dict[str, Any])
async def suspend_user(
    user_id: str,
    request: Request,
    current_user: User = Depends(require_users_suspend),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, user_id)
    if not user or user.deleted_at is not None:
        raise HTTPException(status_code=404, detail="User not found")
    _check_org_scope(current_user, user.organization_id)
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot suspend your own account")

    user.status = "suspended"
    user.updated_by = current_user.id
    await record_audit_log(
        db, actor=current_user, organization_id=user.organization_id, action="user.suspend",
        description=f"User '{user.email}' suspended", resource="users", resource_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return {"success": True, "status": user.status}


@router.post("/{user_id}/reactivate", response_model=Dict[str, Any])
async def reactivate_user(
    user_id: str,
    request: Request,
    current_user: User = Depends(require_users_suspend),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, user_id)
    if not user or user.deleted_at is not None:
        raise HTTPException(status_code=404, detail="User not found")
    _check_org_scope(current_user, user.organization_id)

    user.status = "active"
    user.updated_by = current_user.id
    await record_audit_log(
        db, actor=current_user, organization_id=user.organization_id, action="user.reactivate",
        description=f"User '{user.email}' reactivated", resource="users", resource_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return {"success": True, "status": user.status}


@router.delete("/{user_id}", response_model=Dict[str, Any])
async def delete_user(
    user_id: str,
    request: Request,
    current_user: User = Depends(require_users_delete),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, user_id)
    if not user or user.deleted_at is not None:
        raise HTTPException(status_code=404, detail="User not found")
    _check_org_scope(current_user, user.organization_id)
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    user.deleted_at = datetime.utcnow()
    user.status = "deleted"
    user.updated_by = current_user.id
    await record_audit_log(
        db, actor=current_user, organization_id=user.organization_id, action="user.delete",
        description=f"User '{user.email}' deleted", resource="users", resource_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return {"success": True}


@router.post("/{user_id}/reset-password", response_model=Dict[str, Any])
async def admin_reset_password(
    user_id: str,
    request: Request,
    current_user: User = Depends(require_users_reset_password),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, user_id)
    if not user or user.deleted_at is not None:
        raise HTTPException(status_code=404, detail="User not found")
    _check_org_scope(current_user, user.organization_id)

    raw_token = secrets.token_urlsafe(32)
    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=get_password_hash(raw_token),
        expires_at=datetime.utcnow() + timedelta(hours=2),
    )
    db.add(reset_token)
    await record_audit_log(
        db, actor=current_user, organization_id=user.organization_id, action="user.admin_reset_password",
        description=f"Password reset triggered for '{user.email}' by admin", resource="users", resource_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()

    reset_link = f"{settings.FRONTEND_URL}/auth/reset-password?token={raw_token}"
    email_sent = await send_email(
        to=user.email,
        subject="Your AI-BOS password was reset by an administrator",
        body=f"An administrator has triggered a password reset for your account. Set a new password:\n\n{reset_link}",
    )
    response: Dict[str, Any] = {"success": True}
    if not email_sent and settings.ENVIRONMENT == "development":
        response["reset_link_dev_only"] = reset_link
    return response



class ForcePasswordBody(BaseModel):
    password: str = Field(..., min_length=8)

@router.post("/{user_id}/force-password", response_model=Dict[str, Any])
async def admin_force_password(
    user_id: str,
    body: ForcePasswordBody,
    request: Request,
    current_user: User = Depends(require_users_reset_password),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, user_id)
    if not user or user.deleted_at is not None:
        raise HTTPException(status_code=404, detail="User not found")
    _check_org_scope(current_user, user.organization_id)

    user.password_hash = get_password_hash(body.password)
    user.updated_by = current_user.id
    await record_audit_log(
        db, actor=current_user, organization_id=user.organization_id, action="user.admin_force_password",
        description=f"Password forcibly changed for '{user.email}' by admin", resource="users", resource_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return {"success": True}

class RoleAssignmentBody(BaseModel):
    role_id: str


@router.post("/{user_id}/roles", response_model=Dict[str, Any])
async def assign_additional_role(
    user_id: str,
    body: RoleAssignmentBody,
    request: Request,
    current_user: User = Depends(require_users_assign_role),
    db: AsyncSession = Depends(get_db),
):
    query = select(User).options(selectinload(User.additional_roles)).where(User.id == user_id)
    user = (await db.execute(query)).scalar_one_or_none()
    if not user or user.deleted_at is not None:
        raise HTTPException(status_code=404, detail="User not found")
    _check_org_scope(current_user, user.organization_id)

    role = await _validate_role(body.role_id, db)
    if role.id != user.role_id and role not in user.additional_roles:
        user.additional_roles.append(role)

    await record_audit_log(
        db, actor=current_user, organization_id=user.organization_id, action="user.assign_role",
        description=f"Role '{role.id}' assigned to '{user.email}'", resource="users", resource_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(user)
    return {"success": True, "roles": user.all_role_ids()}


@router.delete("/{user_id}/roles/{role_id}", response_model=Dict[str, Any])
async def remove_additional_role(
    user_id: str,
    role_id: str,
    request: Request,
    current_user: User = Depends(require_users_assign_role),
    db: AsyncSession = Depends(get_db),
):
    query = select(User).options(selectinload(User.additional_roles)).where(User.id == user_id)
    user = (await db.execute(query)).scalar_one_or_none()
    if not user or user.deleted_at is not None:
        raise HTTPException(status_code=404, detail="User not found")
    _check_org_scope(current_user, user.organization_id)

    if role_id == user.role_id:
        raise HTTPException(status_code=400, detail="Cannot remove the user's primary role — assign a different primary role instead")

    user.additional_roles = [r for r in user.additional_roles if r.id != role_id]

    await record_audit_log(
        db, actor=current_user, organization_id=user.organization_id, action="user.remove_role",
        description=f"Role '{role_id}' removed from '{user.email}'", resource="users", resource_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(user)
    return {"success": True, "roles": user.all_role_ids()}
