import logging
from typing import Any, Dict

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
    """Returns billing invoice history. No payment gateway is wired up yet, so there is
    no real invoice ledger to query — return an honest empty list rather than fabricated
    data until a real gateway (Stripe/Razorpay) is integrated and recording charges."""
    return {"invoices": []}


class CheckoutBody(BaseModel):
    plan_id: str
    gateway: str  # stripe or razorpay


@router.post("/checkout", response_model=Dict[str, Any])
async def create_checkout_session(
    body: CheckoutBody,
    current_user: User = Depends(get_current_user),
):
    """Creates a payment gateway checkout session. No gateway credentials are configured
    yet, so this reports the real state rather than returning a fabricated checkout URL."""
    raise HTTPException(
        status_code=503,
        detail=f"Billing gateway '{body.gateway}' is not configured on this server yet.",
    )
