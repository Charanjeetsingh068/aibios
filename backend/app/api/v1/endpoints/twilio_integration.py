import logging
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import verify_twilio_signature
from app.api.v1.endpoints.auth import get_current_user
from app.models.auth import User
from app.models.business import CallLog

logger = logging.getLogger(__name__)
router = APIRouter()


class SendSMSBody(BaseModel):
    to_number: str
    message: str


async def _require_valid_twilio_signature(request: Request) -> Dict[str, Any]:
    """Shared guard for all Twilio webhook endpoints. Fails closed if TWILIO_AUTH_TOKEN
    isn't configured, since there is then no way to verify the request actually came from
    Twilio. Returns the parsed form data on success."""
    form_data = await request.form()
    signature = request.headers.get("x-twilio-signature")
    if not verify_twilio_signature(settings.TWILIO_AUTH_TOKEN, str(request.url), dict(form_data), signature):
        logger.warning("Rejected Twilio webhook request: missing/invalid X-Twilio-Signature.")
        raise HTTPException(status_code=401, detail="Invalid Twilio request signature")
    return form_data


@router.post("/voice")
async def twilio_voice_callback(request: Request):
    """TwiML callback for handling incoming voice calls, greeting user and transferring to supervisor agent."""
    await _require_valid_twilio_signature(request)
    gather_action = f"{settings.API_V1_STR}/twilio/voice/gather"
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joey">Welcome to the AI-BOS Smart Agent Telephony. Please hold while we connect you to our AI supervisor node.</Say>
    <Gather numDigits="1" action="{gather_action}" method="POST" timeout="10">
        <Say voice="Polly.Joey">Press 1 to speak with sales. Press 2 to talk to support. Press any other key to wait.</Say>
    </Gather>
    <Say voice="Polly.Joey">We did not receive any input. Goodbye.</Say>
</Response>"""
    return Response(content=xml_content, media_type="application/xml")


@router.post("/voice/gather")
async def twilio_voice_gather(request: Request):
    """Handles user keypress options."""
    form_data = await _require_valid_twilio_signature(request)
    digits = form_data.get("Digits", "")
    logger.info(f"Twilio gather received digits: {digits}")

    record_action = f"{settings.API_V1_STR}/twilio/voice/record"
    if digits == "1":
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joey">Connecting you to the automated Sales AI. Please state your query after the tone.</Say>
    <Record maxLength="30" playBeep="true" action="{record_action}" method="POST"/>
</Response>"""
    elif digits == "2":
        if not settings.TWILIO_SUPPORT_NUMBER:
            xml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joey">Support routing is not configured yet. Please try again later. Goodbye.</Say>
</Response>"""
        else:
            xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joey">Connecting to the Support knowledge router. Welcome.</Say>
    <Dial>{settings.TWILIO_SUPPORT_NUMBER}</Dial>
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
        form_data = await _require_valid_twilio_signature(request)
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
    except HTTPException:
        raise
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
        raise HTTPException(
            status_code=503,
            detail="Twilio is not configured (missing TWILIO_ACCOUNT_SID/TWILIO_AUTH_TOKEN/TWILIO_PHONE_NUMBER).",
        )

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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send Twilio SMS: {e}")
        raise HTTPException(status_code=502, detail=str(e))
