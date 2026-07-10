import logging
from typing import Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
    Response,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.crypto import decrypt_value
from app.core.database import get_db
from app.models.enterprise_integrations import MetaPage
from app.services.meta_service import retrieve_lead_data
from app.services.meta_sync_service import LeadSyncService
from app.services.meta_webhook_service import MetaWebhookService, WebhookValidator

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("")
async def verify_webhook(
    request: Request,
    hub_mode: Optional[str] = None,
    hub_challenge: Optional[str] = None,
    hub_verify_token: Optional[str] = None,
):
    """Handles Meta Webhook verification requests."""
    if hub_mode == "subscribe" and hub_verify_token == settings.FACEBOOK_APP_SECRET:
        logger.info("Meta Webhook Verification successful.")
        return Response(content=hub_challenge, media_type="text/plain")
    logger.warning("Failed Meta Webhook Verification: token mismatch.")
    raise HTTPException(status_code=403, detail="Verification token mismatch")


@router.post("")
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Receives payloads from Meta for Leads, Messages, etc."""
    payload_body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")
    
    if not WebhookValidator.verify_signature(payload_body, signature):
        logger.warning("Invalid Webhook Signature")
        raise HTTPException(status_code=401, detail="Invalid signature")
        
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
    object_type = data.get("object")
    
    # Log webhook quickly
    log_entry = await MetaWebhookService.log_webhook(
        db=db,
        event_type=object_type,
        payload=payload_body.decode('utf-8'),
        signature=signature
    )

    if object_type == "page":
        # Background process the entries so we return 200 OK fast
        background_tasks.add_task(process_page_entries, data.get("entry", []), log_entry.id)
        
    return Response(content="EVENT_RECEIVED", media_type="text/plain", status_code=200)


async def process_page_entries(entries: list, log_id: str):
    """Background task to process leadgen entries and fetch CRM lead data."""
    # We acquire a new DB session since this is a background task
    from app.core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        for entry in entries:
            page_id = entry.get("id")
            for change in entry.get("changes", []):
                if change.get("field") == "leadgen":
                    leadgen_value = change.get("value", {})
                    leadgen_id = leadgen_value.get("leadgen_id")
                    form_id = leadgen_value.get("form_id")
                    
                    if not leadgen_id:
                        continue
                        
                    # Find organization_id from MetaPage
                    result = await db.execute(select(MetaPage).where(MetaPage.page_id == page_id))
                    meta_page = result.scalar_one_or_none()
                    
                    if not meta_page or not meta_page.page_access_token_encrypted:
                        logger.error(f"Cannot process lead {leadgen_id}: Page {page_id} not connected or missing token.")
                        continue
                        
                    try:
                        page_token = decrypt_value(meta_page.page_access_token_encrypted)
                        raw_data = await retrieve_lead_data(leadgen_id, page_token)
                        
                        await LeadSyncService.process_lead(
                            db=db,
                            organization_id=meta_page.organization_id,
                            meta_page_id=meta_page.id,
                            leadgen_id=leadgen_id,
                            form_id=form_id,
                            raw_data=raw_data
                        )
                    except Exception as e:
                        logger.error(f"Error processing leadgen webhook: {e}")
