import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.pagination import PageParams, pagination_params, apply_sort
from app.api.v1.endpoints.auth import get_current_user, PermissionChecker
from app.models.auth import User, AuditLog

logger = logging.getLogger(__name__)
router = APIRouter()

require_audit_read = PermissionChecker("audit.read")

ALLOWED_SORT_COLUMNS = {"created_at", "action", "resource"}


def _is_platform_admin(user: User) -> bool:
    return "admin.all" in user.all_permission_ids()


def _serialize(entry: AuditLog) -> Dict[str, Any]:
    return {
        "id": entry.id,
        "user_id": entry.user_id,
        "organization_id": entry.organization_id,
        "action": entry.action,
        "description": entry.description,
        "resource": entry.resource,
        "resource_id": entry.resource_id,
        "ip_address": entry.ip_address,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
    }


@router.get("", response_model=Dict[str, Any])
async def list_audit_log(
    current_user: User = Depends(require_audit_read),
    db: AsyncSession = Depends(get_db),
    params: PageParams = Depends(pagination_params),
    action: Optional[str] = None,
    resource: Optional[str] = None,
    organization_id: Optional[str] = None,
):
    query = select(AuditLog)

    if _is_platform_admin(current_user):
        if organization_id:
            query = query.where(AuditLog.organization_id == organization_id)
    else:
        query = query.where(AuditLog.organization_id == current_user.organization_id)

    if action:
        query = query.where(AuditLog.action == action)
    if resource:
        query = query.where(AuditLog.resource == resource)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = apply_sort(query, AuditLog, params, ALLOWED_SORT_COLUMNS, "created_at")
    query = query.offset(params.skip).limit(params.limit)
    items = (await db.execute(query)).scalars().all()

    return {"entries": [_serialize(e) for e in items], "total": total, "skip": params.skip, "limit": params.limit}
