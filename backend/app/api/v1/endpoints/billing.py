import logging
from datetime import datetime
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.v1.endpoints.auth import get_current_user
from app.models.auth import User

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/invoices", response_model=Dict[str, Any])
async def list_invoices(
    current_user: User = Depends(get_current_user),
):
    """Returns billing invoice history list."""
    import random
    invoices = []
    plans = ["Startup Tier", "Professional Tier", "Enterprise Tier"]
    amounts = [49.00, 149.00, 499.00]
    
    # Generate 5 invoices
    for i in range(1, 6):
        inv_date = timedelta_days(i * 30)
        idx = random.randint(0, len(plans) - 1)
        invoices.append({
            "id": f"INV-2026-{1000 + i}",
            "amount": amounts[idx],
            "plan": plans[idx],
            "status": "paid",
            "payment_gateway": "stripe" if i % 2 == 0 else "razorpay",
            "invoice_url": "#",
            "created_at": inv_date.isoformat(),
        })
    return {"invoices": invoices}


class CheckoutBody(BaseModel):
    plan_id: str
    gateway: str  # stripe or razorpay


@router.post("/checkout", response_model=Dict[str, Any])
async def create_checkout_session(
    body: CheckoutBody,
    current_user: User = Depends(get_current_user),
):
    """Simulates payment gateway checkout link generation."""
    session_id = f"sess_{body.gateway}_checkout_12345abcdef"
    if body.gateway == "stripe":
        checkout_url = f"https://checkout.stripe.com/pay/{session_id}"
    else:
        checkout_url = f"https://api.razorpay.com/v1/checkout/{session_id}"
        
    return {
        "success": True,
        "session_id": session_id,
        "checkout_url": checkout_url
    }


def timedelta_days(days: int) -> datetime:
    from datetime import timedelta
    return datetime.utcnow() - timedelta(days=days)
