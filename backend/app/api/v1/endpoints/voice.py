import logging
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.auth import User
from app.models.business import CallLog

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/calls", response_model=Dict[str, Any])
async def list_calls(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(CallLog)
        .where(CallLog.organization_id == current_user.organization_id)
        .order_by(CallLog.created_at.desc())
    )
    res = await db.execute(query)
    items = res.scalars().all()

    # CallLog only persists id/direction/created_at today (no lead linkage, duration, or
    # transcript columns yet) — report those honestly as unavailable rather than fabricating
    # plausible-looking values that don't correspond to any real call.
    logs = [
        {
            "id": c.id,
            "direction": c.direction,
            "lead_name": None,
            "duration_seconds": None,
            "transcript_preview": None,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in items
    ]
    return {"calls": logs}


@router.get("/calls/{call_id}/transcript", response_model=Dict[str, Any])
async def get_call_transcript(
    call_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    c = await db.get(CallLog, call_id)
    if not c or c.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Call log not found")

    # No transcript is persisted for calls yet (requires wiring a real transcription
    # pipeline to the Twilio/voice provider) — report that honestly instead of returning
    # one of a few canned scripts unrelated to the actual call.
    return {
        "call_id": call_id,
        "transcript": None,
        "detail": "No transcript is available for this call yet.",
    }
