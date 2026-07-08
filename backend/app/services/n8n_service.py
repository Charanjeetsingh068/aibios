import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings
from app.core.crypto import decrypt_value, CryptoNotConfiguredError
from app.core.security import sign_hmac_sha256, verify_hmac_sha256_signature
from app.models.enterprise_integrations import N8nConnection, N8nWorkflowMapping, N8nExecutionLog

logger = logging.getLogger(__name__)

RETRYABLE_EXCEPTIONS = (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout)
RETRY_BACKOFF_MINUTES = 5


@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
)
async def _post_webhook(url: str, body: bytes, signature: str) -> httpx.Response:
    async with httpx.AsyncClient(timeout=settings.N8N_DEFAULT_WEBHOOK_TIMEOUT_SECONDS) as client:
        return await client.post(
            url,
            content=body,
            headers={"Content-Type": "application/json", "X-AIBOS-Signature": signature},
        )


def verify_callback_signature(secret: Optional[str], payload: bytes, signature_header: Optional[str]) -> bool:
    return verify_hmac_sha256_signature(secret, payload, signature_header)


async def trigger_workflow(db: AsyncSession, mapping: N8nWorkflowMapping, payload: Dict[str, Any]) -> N8nExecutionLog:
    """Triggers an n8n workflow via its webhook URL, signing the payload with the
    organization's n8n webhook_secret. Always writes an N8nExecutionLog row — success or
    failure — rather than raising, so callers (webhook handlers, lead creation) never break
    on an n8n outage."""
    log = N8nExecutionLog(
        organization_id=mapping.organization_id,
        mapping_id=mapping.id,
        direction="trigger",
        status="pending",
        request_payload=json.dumps(payload),
        triggered_at=datetime.utcnow(),
    )
    db.add(log)
    await db.flush()

    connection = await db.get(N8nConnection, mapping.connection_id)
    if not connection or connection.status != "connected":
        log.status = "failed"
        log.error_detail = "n8n connection is not configured/connected for this organization."
        log.completed_at = datetime.utcnow()
        log.next_retry_at = datetime.utcnow() + timedelta(minutes=RETRY_BACKOFF_MINUTES)
        await db.flush()
        return log

    try:
        secret = decrypt_value(connection.webhook_secret_encrypted)
    except (CryptoNotConfiguredError, ValueError) as e:
        # ValueError covers a decrypt failure from a rotated ENCRYPTION_KEY — a real
        # operational scenario, not a bug, so it must degrade this one trigger rather than
        # bubble up as a 500.
        log.status = "failed"
        log.error_detail = str(e)
        log.completed_at = datetime.utcnow()
        await db.flush()
        return log

    body_bytes = json.dumps(payload).encode("utf-8")
    signature = sign_hmac_sha256(secret, body_bytes)

    try:
        response = await _post_webhook(mapping.n8n_webhook_url, body_bytes, signature)
        log.status_code = response.status_code
        log.response_payload = response.text[:2000] if response.text else None
        log.completed_at = datetime.utcnow()
        if 200 <= response.status_code < 300:
            log.status = "success"
        else:
            log.status = "failed"
            log.error_detail = f"n8n webhook returned HTTP {response.status_code}"
            log.next_retry_at = datetime.utcnow() + timedelta(minutes=RETRY_BACKOFF_MINUTES)
    except RETRYABLE_EXCEPTIONS as e:
        log.status = "failed"
        log.error_detail = f"Connection to n8n failed after retries: {e}"
        log.completed_at = datetime.utcnow()
        log.next_retry_at = datetime.utcnow() + timedelta(minutes=RETRY_BACKOFF_MINUTES)
        logger.warning(f"n8n trigger failed for mapping {mapping.id}: {e}")

    await db.flush()
    return log


async def dispatch_event(db: AsyncSession, organization_id: str, event_name: str, payload: Dict[str, Any]) -> List[N8nExecutionLog]:
    """Looks up active workflow mappings for (organization, trigger_event) and triggers
    each one. Commits its own transaction so a failure here never rolls back the caller's
    primary write (e.g. the Lead that was just created)."""
    result = await db.execute(
        select(N8nWorkflowMapping).where(
            N8nWorkflowMapping.organization_id == organization_id,
            N8nWorkflowMapping.trigger_event == event_name,
            N8nWorkflowMapping.status == "active",
        )
    )
    mappings = result.scalars().all()
    logs = []
    for mapping in mappings:
        logs.append(await trigger_workflow(db, mapping, payload))
    if mappings:
        await db.commit()
    return logs


async def retry_execution(db: AsyncSession, execution_log: N8nExecutionLog) -> N8nExecutionLog:
    """Replays a failed trigger execution, incrementing retry_count (capped at
    max_retries)."""
    if execution_log.retry_count >= execution_log.max_retries:
        raise ValueError(f"Max retries ({execution_log.max_retries}) exceeded for this execution.")
    if not execution_log.mapping_id:
        raise LookupError("This execution has no associated workflow mapping to retry.")

    mapping = await db.get(N8nWorkflowMapping, execution_log.mapping_id)
    if not mapping:
        raise LookupError("The original workflow mapping no longer exists; cannot retry.")

    payload = json.loads(execution_log.request_payload) if execution_log.request_payload else {}
    new_log = await trigger_workflow(db, mapping, payload)
    new_log.retry_count = execution_log.retry_count + 1
    execution_log.retry_count += 1
    await db.commit()
    return new_log
