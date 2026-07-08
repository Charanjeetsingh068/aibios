import logging
import csv
import io
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError

from app.core.database import get_db, verify_postgres, verify_mongo, verify_redis, verify_qdrant
from app.core.config import settings
from app.core import telemetry
from app.models.auth import User, AuditLog
from app.models.business import Lead, Deal, Campaign, TokenUsageEvent

logger = logging.getLogger(__name__)
router = APIRouter()


async def get_current_user_reports(
    db: AsyncSession = Depends(get_db),
    token: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None)
) -> User:
    actual_token = None
    if authorization and authorization.startswith("Bearer "):
        actual_token = authorization.split(" ")[1]
    elif token:
        actual_token = token
        
    if not actual_token:
        raise HTTPException(status_code=401, detail="Unauthorized reports request")
        
    try:
        payload = jwt.decode(actual_token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Unauthorized reports request")
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized reports request")
        
    query = (
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.organization), selectinload(User.role))
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    if not user or user.status != "active":
        raise HTTPException(status_code=401, detail="Unauthorized reports request")
    return user


def _csv_response(rows: List[list], header: List[str], filename_prefix: str) -> StreamingResponse:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(header)
    writer.writerows(rows)
    output.seek(0)
    filename = f"{filename_prefix}_{datetime.utcnow().strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/{report_type}/download")
async def download_report(
    report_type: str,
    format: str = "csv",
    current_user: User = Depends(get_current_user_reports),
    db: AsyncSession = Depends(get_db),
):
    """Generates and downloads a real data report in CSV format."""
    org_id = current_user.organization_id

    if report_type == "leads":
        res = await db.execute(select(Lead).where(Lead.organization_id == org_id))
        rows = [
            [l.id, l.name, l.company or "", l.phone or "", l.email or "", l.source, l.status,
             float(l.value or 0), l.created_at.isoformat() if l.created_at else ""]
            for l in res.scalars().all()
        ]
        return _csv_response(rows, ["ID", "Name", "Company", "Phone", "Email", "Source", "Status", "Value", "Created At"], "leads_report")

    elif report_type == "revenue":
        res = await db.execute(select(Deal).where(Deal.organization_id == org_id))
        rows = [
            [d.id, d.name, d.company or "", d.stage, float(d.value or 0), d.created_at.isoformat() if d.created_at else ""]
            for d in res.scalars().all()
        ]
        return _csv_response(rows, ["ID", "Deal Name", "Company", "Stage", "Value", "Created At"], "revenue_report")

    elif report_type == "campaigns":
        res = await db.execute(select(Campaign).where(Campaign.organization_id == org_id))
        rows = [
            [c.id, c.name, c.channel, c.status, c.progress, c.created_at.isoformat() if c.created_at else ""]
            for c in res.scalars().all()
        ]
        return _csv_response(rows, ["ID", "Campaign Name", "Channel", "Status", "Progress %", "Created At"], "campaign_report")

    elif report_type == "tokens":
        res = await db.execute(select(TokenUsageEvent).where(TokenUsageEvent.organization_id == org_id))
        rows = [
            [t.id, t.input_tokens, t.output_tokens, t.input_tokens + t.output_tokens, t.created_at.isoformat() if t.created_at else ""]
            for t in res.scalars().all()
        ]
        return _csv_response(rows, ["ID", "Input Tokens", "Output Tokens", "Total Tokens", "Created At"], "token_usage_report")

    elif report_type == "audit":
        res = await db.execute(
            select(AuditLog).where(AuditLog.organization_id == org_id).order_by(AuditLog.created_at.desc()).limit(1000)
        )
        rows = [
            [a.id, a.user_id or "", a.action, a.description, a.resource, a.resource_id or "",
             a.ip_address or "", a.created_at.isoformat() if a.created_at else ""]
            for a in res.scalars().all()
        ]
        return _csv_response(rows, ["ID", "User ID", "Action", "Description", "Resource", "Resource ID", "IP Address", "Created At"], "audit_log_report")

    elif report_type == "system":
        postgres_ok, mongo_ok, redis_ok, qdrant_ok = await verify_postgres(), await verify_mongo(), await verify_redis(), await verify_qdrant()
        stats = telemetry.get_stats()
        rows = [
            ["PostgreSQL Connected", postgres_ok],
            ["MongoDB Connected", mongo_ok],
            ["Redis Connected", redis_ok],
            ["Qdrant Connected", qdrant_ok],
            ["API Requests Today", stats["requests_today"]],
            ["Avg Response Time (ms)", stats["avg_response_time_ms"]],
            ["Report Generated At", datetime.utcnow().isoformat()],
        ]
        return _csv_response(rows, ["Metric", "Value"], "system_health_report")

    else:
        raise HTTPException(status_code=400, detail=f"Unknown report type: {report_type}")
