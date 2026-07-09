from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import AuditLog, User


async def record_audit_log(
    db: AsyncSession,
    *,
    actor: Optional[User],
    organization_id: Optional[str],
    action: str,
    description: str,
    resource: str,
    resource_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    commit: bool = False,
) -> AuditLog:
    """Appends one AuditLog row. Does not commit by default — call sites that are already
    inside a larger transaction (create/update/delete) should let their own db.commit()
    persist this alongside the change it describes; pass commit=True for call sites with
    no surrounding transaction of their own."""
    entry = AuditLog(
        user_id=actor.id if actor else None,
        organization_id=organization_id,
        action=action,
        description=description,
        resource=resource,
        resource_id=resource_id,
        ip_address=ip_address,
    )
    db.add(entry)
    if commit:
        await db.commit()
    return entry
