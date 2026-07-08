import logging
import csv
import io
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError

from app.core.database import get_db
from app.core.config import settings
from app.models.auth import User
from app.models.business import Lead, Deal

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


@router.get("/{report_type}/download")
async def download_report(
    report_type: str,
    format: str = "csv",
    current_user: User = Depends(get_current_user_reports),
    db: AsyncSession = Depends(get_db),
):
    """Generates and downloads a real data report in CSV or text format."""
    if report_type == "leads":
        stmt = select(Lead).where(Lead.organization_id == current_user.organization_id)
        res = await db.execute(stmt)
        leads = res.scalars().all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Name", "Company", "Phone", "Email", "Source", "Status", "Value", "Created At"])
        for l in leads:
            writer.writerow([
                l.id, l.name, l.company or "", l.phone or "", l.email or "",
                l.source, l.status, float(l.value or 0),
                l.created_at.isoformat() if l.created_at else ""
            ])
        output.seek(0)
        
        filename = f"leads_report_{datetime.utcnow().strftime('%Y%m%d')}.csv"
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    elif report_type == "revenue":
        stmt = select(Deal).where(Deal.organization_id == current_user.organization_id)
        res = await db.execute(stmt)
        deals = res.scalars().all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Deal Name", "Company", "Stage", "Value", "Created At"])
        for d in deals:
            writer.writerow([
                d.id, d.name, d.company or "", d.stage, float(d.value or 0),
                d.created_at.isoformat() if d.created_at else ""
            ])
        output.seek(0)

        filename = f"revenue_report_{datetime.utcnow().strftime('%Y%m%d')}.csv"
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    else:
        # Default fallback generic report
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Key Metric", "Value"])
        writer.writerow(["Uptime", "Online"])
        writer.writerow(["Timestamp", datetime.utcnow().isoformat()])
        output.seek(0)
        
        filename = f"system_{report_type}_{datetime.utcnow().strftime('%Y%m%d')}.csv"
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
