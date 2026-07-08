import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.auth import User
from app.models.business import CallLog

logger = logging.getLogger(__name__)
router = APIRouter()


async def _seed_calls_if_empty(db: AsyncSession, org_id: str):
    count_stmt = select(func.count(CallLog.id)).where(CallLog.organization_id == org_id)
    count_res = await db.execute(count_stmt)
    if (count_res.scalar() or 0) == 0:
        db.add(CallLog(organization_id=org_id, direction="outbound"))
        db.add(CallLog(organization_id=org_id, direction="inbound"))
        db.add(CallLog(organization_id=org_id, direction="outbound"))
        await db.commit()


@router.get("/calls", response_model=Dict[str, Any])
async def list_calls(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _seed_calls_if_empty(db, current_user.organization_id)
    query = (
        select(CallLog)
        .where(CallLog.organization_id == current_user.organization_id)
        .order_by(CallLog.created_at.desc())
    )
    res = await db.execute(query)
    items = res.scalars().all()

    # Generate mock metadata fields (lead name, duration, recording URL) dynamically
    leads = ["Charanjeet Singh", "Jane Smith", "David Miller", "John Doe"]
    transcripts = [
        "Hello, this is the AI assistant calling from Demo Corp. We noticed you filled out a lead form... Perfect, I will schedule that.",
        "Hi, I wanted to inquire about the professional plan pricing. Yes, 10 agent nodes. Thank you.",
        "AI voice verification test call completed. Latency was 120ms. OpenAI Realtime agent online.",
    ]

    logs = []
    for idx, c in enumerate(items):
        l_idx = idx % len(leads)
        t_idx = idx % len(transcripts)
        logs.append({
            "id": c.id,
            "direction": c.direction,
            "lead_name": leads[l_idx],
            "duration_seconds": 45 + (idx * 27) % 180,
            "transcript_preview": transcripts[t_idx][:60] + "...",
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })
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

    transcripts = [
        "AI: Hello, this is the AI assistant calling from Demo Corp. We noticed you filled out a lead form on our website.\nUser: Yes, I am interested in your services.\nAI: Great! I can schedule a demo session for you tomorrow morning.\nUser: That works for me, thank you.",
        "User: Hi, I wanted to inquire about the professional plan pricing.\nAI: Hello! The professional plan starts at $149 per month and supports up to 10 active agent nodes.\nUser: Great, thank you so much.\nAI: You're welcome! Let us know if you need anything else.",
    ]
    
    # Simple deterministic hash for demo preview
    idx = abs(hash(call_id)) % len(transcripts)
    return {
        "call_id": call_id,
        "transcript": transcripts[idx]
    }
