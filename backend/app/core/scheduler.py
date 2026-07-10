import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()

async def job_refresh_meta_tokens():
    logger.info("Running Token Refresh Job")
    # Stub for token refresh

async def job_retry_webhooks():
    logger.info("Running Webhook Retry Queue Job")
    # Stub for webhook retry

def start_scheduler():
    scheduler.add_job(job_refresh_meta_tokens, IntervalTrigger(hours=24), id='refresh_tokens', replace_existing=True)
    scheduler.add_job(job_retry_webhooks, IntervalTrigger(minutes=5), id='retry_webhooks', replace_existing=True)
    scheduler.start()
    logger.info("Background jobs started.")

def stop_scheduler():
    scheduler.shutdown()
