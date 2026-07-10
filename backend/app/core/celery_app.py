import logging

from celery import Celery

from app.core.config import settings

logger = logging.getLogger(__name__)

redis_password = f":{settings.REDIS_PASSWORD}@" if settings.REDIS_PASSWORD else ""
redis_url = f"redis://{redis_password}{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"

celery_app = Celery(
    "aibios_tasks",
    broker=redis_url,
    backend=redis_url
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    # Dormant until an operator actually runs `celery -A app.core.celery_app beat` alongside
    # a worker — defining the schedule here doesn't start anything on its own. Runs daily
    # since Meta long-lived tokens last ~60 days; a 7-day expires-soon window (see
    # app/services/integration_manager.py) gives ample margin even at this cadence.
    beat_schedule={
        "refresh-expiring-integration-credentials-daily": {
            "task": "refresh_expiring_credentials_task",
            "schedule": 60 * 60 * 24,
        },
    },
)


@celery_app.task(name="prune_audit_logs_task")
def prune_audit_logs():
    """Periodic job task to clean up old audit logs."""
    logger.info("Executing periodic Celery task: Pruning historical audit logs.")
    return {"status": "success", "pruned_count": 0}


@celery_app.task(name="flush_email_queue_task")
def flush_email_queue():
    """Flushes outgoing email queue items."""
    logger.info("Executing Celery background worker: Flushing email queue.")
    return {"status": "success", "sent_count": 0}


@celery_app.task(name="refresh_expiring_credentials_task")
def refresh_expiring_credentials_task():
    """Real token-refresh sweep: finds IntegrationCredential rows expiring within the next
    7 days (across all organizations) and refreshes each via the same
    integration_manager.refresh_meta_credential() used by the manual /refresh endpoint.
    Only meta-provider credentials support refresh today. Requires a Celery beat process
    to actually fire on the schedule above — see docs/integration-layer/integration-manager.md."""
    import asyncio
    from datetime import datetime, timedelta

    from sqlalchemy import select

    from app.core.database import (
        AsyncSessionLocal,
        SqliteSessionLocal,
        is_postgres_offline,
    )
    from app.models.enterprise_integrations import IntegrationCredential
    from app.services.integration_manager import refresh_meta_credential

    async def _run() -> dict:
        use_sqlite = await is_postgres_offline()
        session_factory = SqliteSessionLocal if use_sqlite else AsyncSessionLocal
        refreshed, failed = 0, 0
        async with session_factory() as session:
            cutoff = datetime.utcnow() + timedelta(days=7)
            result = await session.execute(
                select(IntegrationCredential).where(
                    IntegrationCredential.provider == "meta",
                    IntegrationCredential.expires_at.is_not(None),
                    IntegrationCredential.expires_at < cutoff,
                )
            )
            for credential in result.scalars().all():
                await refresh_meta_credential(session, credential)
                if credential.status == "connected":
                    refreshed += 1
                else:
                    failed += 1
            await session.commit()
        return {"status": "success", "refreshed": refreshed, "failed": failed}

    result = asyncio.run(_run())
    logger.info(f"refresh_expiring_credentials_task completed: {result}")
    return result
