import logging
import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.audit import record_audit_log
from app.api.v1.endpoints.auth import get_current_user, PermissionChecker
from app.models.auth import User, Role, Permission

logger = logging.getLogger(__name__)
router = APIRouter()

require_roles_read = PermissionChecker("roles.read")
require_roles_write = PermissionChecker("roles.write")
require_roles_delete = PermissionChecker("roles.delete")
require_roles_assign_permission = PermissionChecker("roles.assign_permission")

ROLE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]{1,49}$")

# Roles seeded by the platform (app/core/database.py seed_database) — protected from
# deletion/rename so PermissionChecker's built-in expectations (e.g. "admin.all" always
# resolving through some role) can't be silently broken via the API.
SYSTEM_ROLE_IDS = {"super_admin", "org_admin", "manager", "sales_executive", "ai_agent", "developer", "auditor", "viewer"}


def _serialize_permission(p: Permission) -> Dict[str, Any]:
    return {"id": p.id, "name": p.name, "description": p.description}


def _serialize_role(role: Role) -> Dict[str, Any]:
    return {
        "id": role.id,
        "name": role.name,
        "description": role.description,
        "is_system": role.id in SYSTEM_ROLE_IDS,
        "permissions": [p.id for p in role.permissions],
        "created_at": role.created_at.isoformat() if role.created_at else None,
        "updated_at": role.updated_at.isoformat() if role.updated_at else None,
    }


@router.get("/permissions", response_model=Dict[str, Any])
async def list_permissions(
    current_user: User = Depends(require_roles_read),
    db: AsyncSession = Depends(get_db),
):
    items = (await db.execute(select(Permission).order_by(Permission.id))).scalars().all()
    return {"permissions": [_serialize_permission(p) for p in items]}


@router.get("", response_model=Dict[str, Any])
async def list_roles(
    current_user: User = Depends(require_roles_read),
    db: AsyncSession = Depends(get_db),
):
    items = (await db.execute(select(Role).order_by(Role.name))).scalars().all()
    return {"roles": [_serialize_role(r) for r in items]}


@router.get("/{role_id}", response_model=Dict[str, Any])
async def get_role(
    role_id: str,
    current_user: User = Depends(require_roles_read),
    db: AsyncSession = Depends(get_db),
):
    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return _serialize_role(role)


class RoleCreateBody(BaseModel):
    id: str = Field(..., description="Slug id, e.g. 'regional_manager'")
    name: str
    description: Optional[str] = None
    permissions: List[str] = []

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not ROLE_ID_PATTERN.match(v):
            raise ValueError("Role id must be lowercase, start with a letter, and contain only letters/digits/underscores")
        return v


@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_role(
    body: RoleCreateBody,
    request: Request,
    current_user: User = Depends(require_roles_write),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.get(Role, body.id)
    if existing:
        raise HTTPException(status_code=409, detail=f"Role '{body.id}' already exists")

    role = Role(id=body.id, name=body.name.strip(), description=body.description)
    if body.permissions:
        perms = (await db.execute(select(Permission).where(Permission.id.in_(body.permissions)))).scalars().all()
        found_ids = {p.id for p in perms}
        missing = set(body.permissions) - found_ids
        if missing:
            raise HTTPException(status_code=400, detail=f"Unknown permission(s): {', '.join(sorted(missing))}")
        role.permissions = list(perms)

    db.add(role)
    await db.flush()
    await record_audit_log(
        db, actor=current_user, organization_id=current_user.organization_id, action="role.create",
        description=f"Role '{role.id}' created", resource="roles", resource_id=role.id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(role)
    return _serialize_role(role)


class RoleUpdateBody(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


@router.patch("/{role_id}", response_model=Dict[str, Any])
async def update_role(
    role_id: str,
    body: RoleUpdateBody,
    request: Request,
    current_user: User = Depends(require_roles_write),
    db: AsyncSession = Depends(get_db),
):
    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    changes = body.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(role, field, value)

    await record_audit_log(
        db, actor=current_user, organization_id=current_user.organization_id, action="role.update",
        description=f"Role '{role.id}' updated", resource="roles", resource_id=role.id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(role)
    return _serialize_role(role)


@router.delete("/{role_id}", response_model=Dict[str, Any])
async def delete_role(
    role_id: str,
    request: Request,
    current_user: User = Depends(require_roles_delete),
    db: AsyncSession = Depends(get_db),
):
    if role_id in SYSTEM_ROLE_IDS:
        raise HTTPException(status_code=400, detail="System roles cannot be deleted")
    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    if role.users:
        raise HTTPException(status_code=409, detail="Cannot delete a role that is still assigned to users")

    await db.delete(role)
    await record_audit_log(
        db, actor=current_user, organization_id=current_user.organization_id, action="role.delete",
        description=f"Role '{role_id}' deleted", resource="roles", resource_id=role_id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return {"success": True}


class PermissionAssignmentBody(BaseModel):
    permission_id: str


@router.post("/{role_id}/permissions", response_model=Dict[str, Any])
async def assign_permission(
    role_id: str,
    body: PermissionAssignmentBody,
    request: Request,
    current_user: User = Depends(require_roles_assign_permission),
    db: AsyncSession = Depends(get_db),
):
    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    permission = await db.get(Permission, body.permission_id)
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")

    if permission not in role.permissions:
        role.permissions.append(permission)

    await record_audit_log(
        db, actor=current_user, organization_id=current_user.organization_id, action="role.assign_permission",
        description=f"Permission '{permission.id}' assigned to role '{role.id}'", resource="roles", resource_id=role.id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(role)
    return _serialize_role(role)


@router.delete("/{role_id}/permissions/{permission_id}", response_model=Dict[str, Any])
async def remove_permission(
    role_id: str,
    permission_id: str,
    request: Request,
    current_user: User = Depends(require_roles_assign_permission),
    db: AsyncSession = Depends(get_db),
):
    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    role.permissions = [p for p in role.permissions if p.id != permission_id]

    await record_audit_log(
        db, actor=current_user, organization_id=current_user.organization_id, action="role.remove_permission",
        description=f"Permission '{permission_id}' removed from role '{role.id}'", resource="roles", resource_id=role.id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(role)
    return _serialize_role(role)
