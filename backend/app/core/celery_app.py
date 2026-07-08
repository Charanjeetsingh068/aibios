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
