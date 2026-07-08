import logging
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.auth import User
from app.models.business import CallLog

logger = logging.getLogger(__name__)
router = APIRouter()


class SendSMSBody(BaseModel):
    to_number: str
    message: str


@router.post("/voice")
async def twilio_voice_callback():
    """TwiML callback for handling incoming voice calls, greeting user and transferring to supervisor agent."""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joey">Welcome to the AI-BOS Smart Agent Telephony. Please hold while we connect you to our AI supervisor node.</Say>
    <Gather numDigits="1" action="/api/v1/twilio/voice/gather" method="POST" timeout="10">
        <Say voice="Polly.Joey">Press 1 to speak with sales. Press 2 to talk to support. Press any other key to wait.</Say>
    </Gather>
    <Say voice="Polly.Joey">We did not receive any input. Goodbye.</Say>
</Response>"""
    return Response(content=xml_content, media_type="application/xml")


@router.post("/voice/gather")
async def twilio_voice_gather(request: Request):
    """Handles user keypress options."""
    form_data = await request.form()
    digits = form_data.get("Digits", "")
    logger.info(f"Twilio gather received digits: {digits}")
    
    if digits == "1":
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joey">Connecting you to the automated Sales AI. Please state your query after the tone.</Say>
    <Record maxLength="30" playBeep="true" action="/api/v1/twilio/voice/record" method="POST"/>
</Response>"""
    elif digits == "2":
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joey">Connecting to the Support knowledge router. Welcome.</Say>
    <Dial>+15550199000</Dial>
</Response>"""
    else:
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joey">Option not recognized. Goodbye.</Say>
</Response>"""
    return Response(content=xml, media_type="application/xml")


@router.post("/voice/events")
async def twilio_voice_events(request: Request, db: AsyncSession = Depends(get_db)):
    """Receives and logs calls state updates from Twilio (ringing, answered, duration, cost)."""
    try:
        form_data = await request.form()
        call_sid = form_data.get("CallSid")
        call_status = form_data.get("CallStatus")
        duration = form_data.get("CallDuration")
        from_num = form_data.get("From")
        direction = form_data.get("Direction", "inbound")
        
        logger.info(f"Twilio call state event: {call_sid} - Status: {call_status} - Duration: {duration}s")
        
        if call_status == "completed" and from_num:
            from app.models.auth import Organization
            org_stmt = select(Organization).limit(1)
            org_res = await db.execute(org_stmt)
            org = org_res.scalar_one_or_none()
            
            if org:
                call = CallLog(
                    organization_id=org.id,
                    direction=direction,
                )
                db.add(call)
                await db.commit()
    except Exception as e:
        logger.error(f"Error logging Twilio voice call event: {e}")
        
    return {"status": "event_logged"}


@router.post("/sms/send", response_model=Dict[str, Any])
async def send_sms_message(
    body: SendSMSBody,
    current_user: User = Depends(get_current_user),
):
    """Sends SMS using Twilio Client REST API."""
    sid = settings.TWILIO_ACCOUNT_SID
    token = settings.TWILIO_AUTH_TOKEN
    from_num = settings.TWILIO_PHONE_NUMBER
    
    if not sid or not token or not from_num:
        logger.warning("Twilio parameters missing. Simulating successful SMS dispatch.")
        return {
            "success": True,
            "detail": "Twilio not configured. SMS simulated successfully.",
            "to": body.to_number
        }
        
    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    auth = (sid, token)
    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(
                url,
                auth=auth,
                data={
                    "To": body.to_number,
                    "From": from_num,
                    "Body": body.message
                },
                timeout=5.0
            )
            if res.status_code in (200, 201):
                return {"success": True, "data": res.json()}
            else:
                raise HTTPException(status_code=res.status_code, detail=res.text)
    except Exception as e:
        logger.error(f"Failed to send Twilio SMS: {e}")
        raise HTTPException(status_code=500, detail=str(e))
