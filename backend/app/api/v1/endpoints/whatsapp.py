import json
import logging
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from pydantic import BaseModel
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import verify_meta_signature
from app.api.v1.endpoints.auth import get_current_user
from app.models.auth import User
from app.models.business import Lead

logger = logging.getLogger(__name__)
router = APIRouter()


class SendWAMessageBody(BaseModel):
    to_number: str
    message_text: str


class SendWATemplateBody(BaseModel):
    to_number: str
    template_name: str
    language_code: str = "en"


@router.get("/webhook")
async def verify_whatsapp_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):
    """Meta webhook verification endpoint."""
    expected_token = settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN
    if expected_token and hub_mode == "subscribe" and hub_verify_token == expected_token:
        logger.info("WhatsApp webhook verified successfully.")
        return Response(content=hub_challenge, media_type="text/plain")
    else:
        logger.warning("WhatsApp webhook verification failed.")
        raise HTTPException(status_code=403, detail="Verification token mismatch")


@router.post("/webhook")
async def receive_whatsapp_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Receives and parses incoming messages webhook events from Meta WhatsApp Cloud API."""
    raw_body = await request.body()
    signature = request.headers.get("x-hub-signature-256")
    if not verify_meta_signature(settings.WHATSAPP_APP_SECRET, raw_body, signature):
        logger.warning("Rejected WhatsApp webhook: missing/invalid X-Hub-Signature-256.")
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        body = json.loads(raw_body)
        logger.info(f"Received WhatsApp webhook body: {body}")
        
        entries = body.get("entry", [])
        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                messages = value.get("messages", [])
                for msg in messages:
                    from_num = msg.get("from")
                    text_obj = msg.get("text", {})
                    msg_text = text_obj.get("body", "")
                    contacts = value.get("contacts", [])
                    contact_name = contacts[0].get("profile", {}).get("name", "WhatsApp Lead") if contacts else "WhatsApp Lead"
                    
                    if from_num and msg_text:
                        from app.models.auth import Organization
                        org_stmt = select(Organization).limit(1)
                        org_res = await db.execute(org_stmt)
                        org = org_res.scalar_one_or_none()
                        
                        if org:
                            lead = Lead(
                                organization_id=org.id,
                                name=contact_name,
                                phone=from_num,
                                source="whatsapp",
                                status="new",
                                value=0.0
                            )
                            db.add(lead)
                            await db.commit()
                            logger.info(f"Automatically created WhatsApp lead: {contact_name} ({from_num})")
    except Exception as e:
        logger.error(f"Error parsing WhatsApp webhook: {e}")
        
    return {"status": "event_received"}


@router.post("/send", response_model=Dict[str, Any])
async def send_whatsapp_message(
    body: SendWAMessageBody,
    current_user: User = Depends(get_current_user),
):
    """Sends a text message using Meta WhatsApp Cloud API."""
    token = settings.WHATSAPP_ACCESS_TOKEN
    phone_id = settings.WHATSAPP_PHONE_NUMBER_ID
    
    if not token or not phone_id:
        raise HTTPException(
            status_code=503,
            detail="WhatsApp is not configured (missing WHATSAPP_ACCESS_TOKEN/WHATSAPP_PHONE_NUMBER_ID).",
        )

    url = f"https://graph.facebook.com/v18.0/{phone_id}/messages"
    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(
                url,
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={
                    "messaging_product": "whatsapp",
                    "to": body.to_number,
                    "type": "text",
                    "text": {"body": body.message_text}
                },
                timeout=5.0
            )
            if res.status_code == 200:
                return {"success": True, "data": res.json()}
            else:
                raise HTTPException(status_code=res.status_code, detail=res.text)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send WhatsApp message: {e}")
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/send-template", response_model=Dict[str, Any])
async def send_whatsapp_template(
    body: SendWATemplateBody,
    current_user: User = Depends(get_current_user),
):
    """Sends a pre-registered Meta message template to client."""
    token = settings.WHATSAPP_ACCESS_TOKEN
    phone_id = settings.WHATSAPP_PHONE_NUMBER_ID
    
    if not token or not phone_id:
        raise HTTPException(
            status_code=503,
            detail="WhatsApp is not configured (missing WHATSAPP_ACCESS_TOKEN/WHATSAPP_PHONE_NUMBER_ID).",
        )

    url = f"https://graph.facebook.com/v18.0/{phone_id}/messages"
    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(
                url,
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={
                    "messaging_product": "whatsapp",
                    "to": body.to_number,
                    "type": "template",
                    "template": {
                        "name": body.template_name,
                        "language": {"code": body.language_code}
                    }
                },
                timeout=5.0
            )
            if res.status_code == 200:
                return {"success": True, "data": res.json()}
            else:
                raise HTTPException(status_code=res.status_code, detail=res.text)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send WhatsApp template: {e}")
        raise HTTPException(status_code=502, detail=str(e))
