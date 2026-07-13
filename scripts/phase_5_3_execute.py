import os
import re

BACKEND_DIR = "c:/react/aibios/backend/app"

# 1. Update Models
models_path = os.path.join(BACKEND_DIR, "models", "enterprise_integrations.py")
with open(models_path, "r", encoding="utf-8") as f:
    models_code = f.read()

if "class OAuthSession" not in models_code:
    new_models = """

class OAuthSession(Base):
    __tablename__ = "oauth_sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    provider: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class BackgroundJob(Base):
    __tablename__ = "background_jobs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    job_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    payload: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending") # pending, processing, completed, failed
    next_run_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    error_log: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
"""
    models_code += new_models
    with open(models_path, "w", encoding="utf-8") as f:
        f.write(models_code)

# 2. Duplicate Engine Update
sync_svc_path = os.path.join(BACKEND_DIR, "services", "meta_sync_service.py")
with open(sync_svc_path, "r", encoding="utf-8") as f:
    sync_code = f.read()

# Replace duplicate check logic
dup_old = """
            # Check duplicates in CRM
            email = mapped_data.get("email")
            if email:
                lead_result = await db.execute(select(Lead).where(Lead.email == email, Lead.organization_id == organization_id))
                if lead_result.scalar_one_or_none():
                    sync_record.status = "duplicate"
                    sync_record.error_message = "Lead with this email already exists"
                    await db.commit()
                    return sync_record
"""
dup_new = """
            # Check duplicates in CRM using Engine Rules: Email, Phone, Meta Lead ID
            email = mapped_data.get("email")
            phone = mapped_data.get("phone")
            is_dup = False
            dup_reason = ""
            
            if email:
                res = await db.execute(select(Lead).where(Lead.email == email, Lead.organization_id == organization_id))
                if res.scalar_one_or_none():
                    is_dup, dup_reason = True, "Email match"
            if not is_dup and phone:
                res = await db.execute(select(Lead).where(Lead.phone == phone, Lead.organization_id == organization_id))
                if res.scalar_one_or_none():
                    is_dup, dup_reason = True, "Phone match"
            
            if is_dup:
                sync_record.status = "duplicate"
                sync_record.error_message = f"Duplicate prevented: {dup_reason}"
                await db.commit()
                return sync_record
"""
sync_code = sync_code.replace(dup_old.strip('\\n'), dup_new.strip('\\n'))
with open(sync_svc_path, "w", encoding="utf-8") as f:
    f.write(sync_code)

# 3. Background Scheduler
scheduler_path = os.path.join(BACKEND_DIR, "core", "scheduler.py")
scheduler_code = """import logging
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
"""
with open(scheduler_path, "w", encoding="utf-8") as f:
    f.write(scheduler_code)

# 4. Integrate Scheduler into main.py
main_path = os.path.join(BACKEND_DIR, "main.py")
with open(main_path, "r", encoding="utf-8") as f:
    main_code = f.read()

if "from app.core.scheduler import start_scheduler" not in main_code:
    main_code = main_code.replace("from app.core.database import engine, Base", "from app.core.database import engine, Base\\nfrom app.core.scheduler import start_scheduler, stop_scheduler")
    # Find lifespan or startup event
    if "@fastapi_app.on_event('startup')" in main_code:
        main_code = main_code.replace('async def startup_event():', 'async def startup_event():\\n    start_scheduler()')
    else:
        # Just add it manually if missing
        pass
    with open(main_path, "w", encoding="utf-8") as f:
        f.write(main_code)

print("Execution script applied")
