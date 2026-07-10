import logging
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import PermissionChecker
from app.core.audit import record_audit_log
from app.core.database import get_db
from app.core.pagination import PageParams, apply_sort, pagination_params
from app.models.auth import Organization, User

logger = logging.getLogger(__name__)
router = APIRouter()

require_org_read = PermissionChecker("organizations.read")
require_org_write = PermissionChecker("organizations.write")
require_org_delete = PermissionChecker("organizations.delete")
require_org_suspend = PermissionChecker("organizations.suspend")

ALLOWED_SORT_COLUMNS = {"name", "slug", "status", "created_at", "updated_at"}


def _serialize(org: Organization) -> Dict[str, Any]:
    return {
        "id": org.id,
        "name": org.name,
        "slug": org.slug,
        "status": org.status,
        "gst_number": org.gst_number,
        "address": org.address,
        "timezone": org.timezone,
        "brand_color": org.brand_color,
        "subscription_plan": org.subscription_plan,
        "created_at": org.created_at.isoformat() if org.created_at else None,
        "updated_at": org.updated_at.isoformat() if org.updated_at else None,
    }


@router.get("", response_model=Dict[str, Any])
async def list_organizations(
    current_user: User = Depends(require_org_read),
    db: AsyncSession = Depends(get_db),
    params: PageParams = Depends(pagination_params),
):
    query = select(Organization).where(Organization.deleted_at.is_(None))
    if params.search:
        like = f"%{params.search}%"
        query = query.where(or_(Organization.name.ilike(like), Organization.slug.ilike(like)))

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = apply_sort(query, Organization, params, ALLOWED_SORT_COLUMNS, "created_at")
    query = query.offset(params.skip).limit(params.limit)
    items = (await db.execute(query)).scalars().all()

    return {"organizations": [_serialize(o) for o in items], "total": total, "skip": params.skip, "limit": params.limit}


@router.get("/{org_id}", response_model=Dict[str, Any])
async def get_organization(
    org_id: str,
    current_user: User = Depends(require_org_read),
    db: AsyncSession = Depends(get_db),
):
    org = await db.get(Organization, org_id)
    if not org or org.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return _serialize(org)


class OrganizationCreateBody(BaseModel):
    name: str
    slug: str
    gst_number: Optional[str] = None
    address: Optional[str] = None
    timezone: Optional[str] = "Asia/Kolkata"
    brand_color: Optional[str] = "#3b82f6"
    subscription_plan: Optional[str] = "enterprise"


@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_organization(
    body: OrganizationCreateBody,
    request: Request,
    current_user: User = Depends(require_org_write),
    db: AsyncSession = Depends(get_db),
):
    existing = (await db.execute(select(Organization).where(Organization.slug == body.slug))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="An organization with this slug already exists")

    org = Organization(
        name=body.name.strip(),
        slug=body.slug.strip().lower(),
        gst_number=body.gst_number,
        address=body.address,
        timezone=body.timezone,
        brand_color=body.brand_color,
        subscription_plan=body.subscription_plan,
        status="active",
        created_by=current_user.id,
        updated_by=current_user.id,
    )
    db.add(org)
    await db.flush()
    await record_audit_log(
        db, actor=current_user, organization_id=org.id, action="organization.create",
        description=f"Organization '{org.name}' created", resource="organizations", resource_id=org.id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(org)
    return _serialize(org)


class OrganizationUpdateBody(BaseModel):
    name: Optional[str] = None
    gst_number: Optional[str] = None
    address: Optional[str] = None
    timezone: Optional[str] = None
    brand_color: Optional[str] = None
    subscription_plan: Optional[str] = None


@router.patch("/{org_id}", response_model=Dict[str, Any])
async def update_organization(
    org_id: str,
    body: OrganizationUpdateBody,
    request: Request,
    current_user: User = Depends(require_org_write),
    db: AsyncSession = Depends(get_db),
):
    org = await db.get(Organization, org_id)
    if not org or org.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Organization not found")

    changes = body.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(org, field, value)
    org.updated_by = current_user.id

    await record_audit_log(
        db, actor=current_user, organization_id=org.id, action="organization.update",
        description=f"Organization '{org.name}' updated ({', '.join(changes.keys()) or 'no fields'})",
        resource="organizations", resource_id=org.id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(org)
    return _serialize(org)


@router.post("/{org_id}/suspend", response_model=Dict[str, Any])
async def suspend_organization(
    org_id: str,
    request: Request,
    current_user: User = Depends(require_org_suspend),
    db: AsyncSession = Depends(get_db),
):
    org = await db.get(Organization, org_id)
    if not org or org.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Organization not found")

    org.status = "suspended"
    org.updated_by = current_user.id
    await record_audit_log(
        db, actor=current_user, organization_id=org.id, action="organization.suspend",
        description=f"Organization '{org.name}' suspended", resource="organizations", resource_id=org.id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return {"success": True, "status": org.status}


@router.post("/{org_id}/reactivate", response_model=Dict[str, Any])
async def reactivate_organization(
    org_id: str,
    request: Request,
    current_user: User = Depends(require_org_suspend),
    db: AsyncSession = Depends(get_db),
):
    org = await db.get(Organization, org_id)
    if not org or org.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Organization not found")

    org.status = "active"
    org.updated_by = current_user.id
    await record_audit_log(
        db, actor=current_user, organization_id=org.id, action="organization.reactivate",
        description=f"Organization '{org.name}' reactivated", resource="organizations", resource_id=org.id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return {"success": True, "status": org.status}


@router.delete("/{org_id}", response_model=Dict[str, Any])
async def delete_organization(
    org_id: str,
    request: Request,
    current_user: User = Depends(require_org_delete),
    db: AsyncSession = Depends(get_db),
):
    org = await db.get(Organization, org_id)
    if not org or org.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Organization not found")

    org.deleted_at = datetime.utcnow()
    org.status = "deleted"
    org.updated_by = current_user.id
    await record_audit_log(
        db, actor=current_user, organization_id=org.id, action="organization.delete",
        description=f"Organization '{org.name}' deleted", resource="organizations", resource_id=org.id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return {"success": True}
