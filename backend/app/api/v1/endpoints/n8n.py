import json
import logging
import secrets
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.crypto import encrypt_value, decrypt_value, CryptoNotConfiguredError
from app.api.v1.endpoints.auth import get_current_user, PermissionChecker
from app.models.auth import User
from app.models.enterprise_integrations import N8nConnection, N8nWorkflowMapping, N8nExecutionLog
from app.services import n8n_service

logger = logging.getLogger(__name__)
router = APIRouter()

require_n8n_write = PermissionChecker("integrations:n8n:write")
require_integrations_read = PermissionChecker("integrations:read")


class ConnectionBody(BaseModel):
    base_url: str
    api_key: Optional[str] = None


class WorkflowMappingBody(BaseModel):
    name: str
    trigger_event: str
    n8n_webhook_url: str
    n8n_workflow_id: Optional[str] = None
    field_mapping: Optional[Dict[str, Any]] = None


class WorkflowMappingPatchBody(BaseModel):
    name: Optional[str] = None
    trigger_event: Optional[str] = None
    n8n_webhook_url: Optional[str] = None
    n8n_workflow_id: Optional[str] = None
    field_mapping: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


class TriggerBody(BaseModel):
    payload: Optional[Dict[str, Any]] = None


def _serialize_connection(c: N8nConnection) -> Dict[str, Any]:
    return {
        "id": c.id,
        "base_url": c.base_url,
        "connection_token": c.connection_token,
        "webhook_callback_url_path": f"/api/v1/n8n/webhook/{c.connection_token}",
        "status": c.status,
        "last_error": c.last_error,
        "has_api_key": bool(c.api_key_encrypted),
    }


def _serialize_mapping(m: N8nWorkflowMapping) -> Dict[str, Any]:
    return {
        "id": m.id,
        "name": m.name,
        "trigger_event": m.trigger_event,
        "n8n_webhook_url": m.n8n_webhook_url,
        "n8n_workflow_id": m.n8n_workflow_id,
        "field_mapping": json.loads(m.field_mapping_json) if m.field_mapping_json else None,
        "status": m.status,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    }


def _serialize_execution(e: N8nExecutionLog) -> Dict[str, Any]:
    return {
        "id": e.id,
        "mapping_id": e.mapping_id,
        "direction": e.direction,
        "status": e.status,
        "status_code": e.status_code,
        "error_detail": e.error_detail,
        "retry_count": e.retry_count,
        "max_retries": e.max_retries,
        "next_retry_at": e.next_retry_at.isoformat() if e.next_retry_at else None,
        "triggered_at": e.triggered_at.isoformat() if e.triggered_at else None,
        "completed_at": e.completed_at.isoformat() if e.completed_at else None,
    }


async def _get_org_connection(db: AsyncSession, organization_id: str) -> Optional[N8nConnection]:
    result = await db.execute(select(N8nConnection).where(N8nConnection.organization_id == organization_id))
    return result.scalar_one_or_none()


@router.post("/connection", response_model=Dict[str, Any])
async def upsert_connection(
    body: ConnectionBody,
    current_user: User = Depends(require_n8n_write),
    db: AsyncSession = Depends(get_db),
):
    """Configures this organization's n8n instance. Generates (or preserves) a per-org
    webhook_secret used to sign outbound triggers and verify inbound callbacks."""
    connection = await _get_org_connection(db, current_user.organization_id)
    is_new = connection is None
    if not connection:
        connection = N8nConnection(
            organization_id=current_user.organization_id,
            base_url=body.base_url,
            webhook_secret_encrypted="",  # set below
        )
        db.add(connection)

    connection.base_url = body.base_url
    if body.api_key:
        try:
            connection.api_key_encrypted = encrypt_value(body.api_key)
        except (CryptoNotConfiguredError, ValueError):
            raise HTTPException(status_code=503, detail="Stored credential could not be decrypted (encryption not configured, or ENCRYPTION_KEY was rotated).")

    if is_new or not connection.webhook_secret_encrypted:
        try:
            connection.webhook_secret_encrypted = encrypt_value(secrets.token_urlsafe(32))
        except (CryptoNotConfiguredError, ValueError):
            raise HTTPException(status_code=503, detail="Stored credential could not be decrypted (encryption not configured, or ENCRYPTION_KEY was rotated).")

    connection.status = "connected"
    connection.last_error = None
    await db.commit()
    return _serialize_connection(connection)


@router.get("/connection", response_model=Dict[str, Any])
async def get_connection(
    current_user: User = Depends(require_integrations_read),
    db: AsyncSession = Depends(get_db),
):
    connection = await _get_org_connection(db, current_user.organization_id)
    if not connection:
        raise HTTPException(status_code=404, detail="n8n is not connected for this organization.")
    return _serialize_connection(connection)


@router.delete("/connection", response_model=Dict[str, Any])
async def delete_connection(
    current_user: User = Depends(require_n8n_write),
    db: AsyncSession = Depends(get_db),
):
    connection = await _get_org_connection(db, current_user.organization_id)
    if not connection:
        raise HTTPException(status_code=404, detail="n8n is not connected for this organization.")
    await db.delete(connection)
    await db.commit()
    return {"status": "disconnected"}


@router.get("/workflows", response_model=Dict[str, Any])
async def list_workflows(
    current_user: User = Depends(require_integrations_read),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(N8nWorkflowMapping).where(N8nWorkflowMapping.organization_id == current_user.organization_id))
    return {"workflows": [_serialize_mapping(m) for m in result.scalars().all()]}


@router.post("/workflows", response_model=Dict[str, Any])
async def create_workflow(
    body: WorkflowMappingBody,
    current_user: User = Depends(require_n8n_write),
    db: AsyncSession = Depends(get_db),
):
    connection = await _get_org_connection(db, current_user.organization_id)
    if not connection:
        raise HTTPException(status_code=409, detail="Configure an n8n connection first via POST /n8n/connection.")

    mapping = N8nWorkflowMapping(
        organization_id=current_user.organization_id,
        connection_id=connection.id,
        name=body.name,
        trigger_event=body.trigger_event,
        n8n_webhook_url=body.n8n_webhook_url,
        n8n_workflow_id=body.n8n_workflow_id,
        field_mapping_json=json.dumps(body.field_mapping) if body.field_mapping is not None else None,
    )
    db.add(mapping)
    await db.commit()
    return _serialize_mapping(mapping)


@router.patch("/workflows/{workflow_id}", response_model=Dict[str, Any])
async def update_workflow(
    workflow_id: str,
    body: WorkflowMappingPatchBody,
    current_user: User = Depends(require_n8n_write),
    db: AsyncSession = Depends(get_db),
):
    mapping = await db.get(N8nWorkflowMapping, workflow_id)
    if not mapping or mapping.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Workflow mapping not found.")

    if body.name is not None:
        mapping.name = body.name
    if body.trigger_event is not None:
        mapping.trigger_event = body.trigger_event
    if body.n8n_webhook_url is not None:
        mapping.n8n_webhook_url = body.n8n_webhook_url
    if body.n8n_workflow_id is not None:
        mapping.n8n_workflow_id = body.n8n_workflow_id
    if body.field_mapping is not None:
        mapping.field_mapping_json = json.dumps(body.field_mapping)
    if body.status is not None:
        mapping.status = body.status

    await db.commit()
    return _serialize_mapping(mapping)


@router.delete("/workflows/{workflow_id}", response_model=Dict[str, Any])
async def delete_workflow(
    workflow_id: str,
    current_user: User = Depends(require_n8n_write),
    db: AsyncSession = Depends(get_db),
):
    mapping = await db.get(N8nWorkflowMapping, workflow_id)
    if not mapping or mapping.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Workflow mapping not found.")
    await db.delete(mapping)
    await db.commit()
    return {"status": "deleted"}


@router.post("/workflows/{workflow_id}/trigger", response_model=Dict[str, Any])
async def trigger_workflow_manually(
    workflow_id: str,
    body: TriggerBody,
    current_user: User = Depends(require_n8n_write),
    db: AsyncSession = Depends(get_db),
):
    mapping = await db.get(N8nWorkflowMapping, workflow_id)
    if not mapping or mapping.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Workflow mapping not found.")

    log = await n8n_service.trigger_workflow(db, mapping, body.payload or {"test": True, "triggered_by": current_user.id})
    await db.commit()
    return _serialize_execution(log)


@router.post("/webhook/{connection_token}", response_model=Dict[str, Any])
async def receive_n8n_callback(
    connection_token: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Inbound callback receiver — n8n calls this to report workflow completion back to
    AI-BOS. Signature-verified against the organization's webhook_secret (real HMAC-SHA256,
    fails closed)."""
    result = await db.execute(select(N8nConnection).where(N8nConnection.connection_token == connection_token))
    connection = result.scalar_one_or_none()
    if not connection:
        raise HTTPException(status_code=404, detail="Unknown connection token.")

    raw_body = await request.body()
    signature = request.headers.get("x-aibos-signature")
    try:
        secret = decrypt_value(connection.webhook_secret_encrypted)
    except (CryptoNotConfiguredError, ValueError):
        raise HTTPException(status_code=503, detail="Stored credential could not be decrypted (encryption not configured, or ENCRYPTION_KEY was rotated).")

    if not n8n_service.verify_callback_signature(secret, raw_body, signature):
        logger.warning(f"Rejected n8n callback for connection {connection.id}: invalid/missing X-AIBOS-Signature.")
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        body = json.loads(raw_body) if raw_body else {}
    except Exception:
        body = {}

    mapping_id = body.get("mapping_id")
    log = N8nExecutionLog(
        organization_id=connection.organization_id,
        mapping_id=mapping_id,
        direction="callback",
        status="success",
        request_payload=raw_body.decode("utf-8", errors="ignore")[:2000] if raw_body else None,
        triggered_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
    )
    db.add(log)
    await db.commit()
    return {"status": "received"}


@router.get("/executions", response_model=Dict[str, Any])
async def list_executions(
    mapping_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    current_user: User = Depends(require_integrations_read),
    db: AsyncSession = Depends(get_db),
):
    query = select(N8nExecutionLog).where(N8nExecutionLog.organization_id == current_user.organization_id)
    if mapping_id:
        query = query.where(N8nExecutionLog.mapping_id == mapping_id)
    if status_filter:
        query = query.where(N8nExecutionLog.status == status_filter)
    query = query.order_by(N8nExecutionLog.triggered_at.desc())

    result = await db.execute(query)
    return {"executions": [_serialize_execution(e) for e in result.scalars().all()]}


@router.post("/executions/{execution_id}/retry", response_model=Dict[str, Any])
async def retry_execution(
    execution_id: str,
    current_user: User = Depends(require_n8n_write),
    db: AsyncSession = Depends(get_db),
):
    execution = await db.get(N8nExecutionLog, execution_id)
    if not execution or execution.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Execution not found.")

    try:
        new_log = await n8n_service.retry_execution(db, execution)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return _serialize_execution(new_log)
