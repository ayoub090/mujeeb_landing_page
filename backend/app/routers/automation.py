from __future__ import annotations

import hmac
import json
import uuid
from datetime import datetime, UTC
from typing import Any

from decimal import Decimal
from fastapi import APIRouter, Header, HTTPException, status, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_session
from app.models import Message, Order, OrderStatus
from app.services.sheets import sync_order_to_google_sheet
from app.services.llm import LLMNotConfigured, draft_customer_message
from app.services.store_sync import sync_order_to_store
from app.services.quota import consume_confirmation_credit

router = APIRouter(prefix="/api/automation", tags=["automation"])


class DraftMessageInput(BaseModel):
    # n8n can deliver the webhook body as an object or as a serialized value.
    # Keep the boundary permissive and normalize it before sending to the LLM.
    order: Any = Field(default_factory=dict)
    language: str = Field(default="ar", min_length=2, max_length=8)


class ApplyDecisionInput(BaseModel):
    """The normalized decision emitted by n8n/OpenRouter.

    The endpoint is intentionally idempotent: n8n may retry a webhook and the
    same decision can safely be applied again.
    """
    order_id: uuid.UUID | None = None
    store_id: uuid.UUID | None = None
    external_order_id: str | None = Field(default=None, max_length=180)
    action: str = Field(default="", max_length=40)
    status: str = Field(default="pending", max_length=40)
    risk_score: int | None = Field(default=None, ge=0, le=100)
    customer_message_ar: str | None = Field(default=None, max_length=4000)
    customer_message_en: str | None = Field(default=None, max_length=4000)
    location_required: bool | None = None
    gps_lat: Decimal | None = Field(default=None, ge=-90, le=90)
    gps_lng: Decimal | None = Field(default=None, ge=-180, le=180)
    upsell_offer: Any = None
    dashboard_note: str | None = Field(default=None, max_length=2000)


def _safe_status(value: str) -> OrderStatus:
    aliases = {"confirm": "confirmed", "confirm_cod": "confirmed", "cancel": "cancelled", "follow_up": "human_follow_up"}
    normalized = aliases.get(value.strip().lower(), value.strip().lower())
    try:
        return OrderStatus(normalized)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Unsupported order status: {value}") from exc


@router.post("/draft-message")
async def draft_message(
    payload: dict[str, Any],
    x_n8n_secret: str | None = Header(default=None),
):
    settings = get_settings()
    if not settings.n8n_shared_secret or not x_n8n_secret or not hmac.compare_digest(
        x_n8n_secret, settings.n8n_shared_secret
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid automation secret")
    try:
        raw_order = payload.get("order", {})
        order = raw_order if isinstance(raw_order, dict) else {"raw": raw_order}
        language = str(payload.get("language", "ar"))[:8] or "ar"
        message = await draft_customer_message(order=order, language=language)
    except LLMNotConfigured as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    return {"status": "ok", "message": message, "model": settings.openrouter_model}


@router.post("/apply-decision")
async def apply_decision(
    payload: ApplyDecisionInput,
    x_n8n_secret: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
):
    """Persist the LLM result so the dashboard is the source of truth.

    n8n calls this after OpenRouter. No customer-facing send is performed here;
    WhatsApp delivery remains an explicit Meta/n8n step and can be retried
    without duplicating or corrupting the order.
    """
    settings = get_settings()
    if not settings.n8n_shared_secret or not x_n8n_secret or not hmac.compare_digest(x_n8n_secret, settings.n8n_shared_secret):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid automation secret")
    if not payload.order_id and not (payload.store_id and payload.external_order_id):
        raise HTTPException(status_code=422, detail="order_id or store_id + external_order_id is required")

    if payload.order_id:
        order = await session.scalar(select(Order).where(Order.id == payload.order_id))
    else:
        order = await session.scalar(select(Order).where(
            Order.store_id == payload.store_id,
            Order.external_order_id == payload.external_order_id,
        ))
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Accept both the normalized n8n object and the raw JSON string returned by
    # OpenRouter. This keeps the workflow resilient when a provider wraps JSON
    # in a markdown code fence.
    decision = {}
    if payload.action.strip().startswith("{") or "```json" in payload.action:
        candidate = payload.action.replace("```json", "").replace("```", "").strip()
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                decision = parsed
        except json.JSONDecodeError:
            decision = {}
    resolved_status = str(decision.get("status") or payload.status)
    next_status = _safe_status(resolved_status)
    # n8n retries must be harmless: the credit is consumed only on the first
    # successful transition into confirmed status.
    if next_status == OrderStatus.confirmed and order.status != OrderStatus.confirmed:
        await consume_confirmation_credit(order.store_id, session)
    order.status = next_status
    resolved_risk = decision.get("risk_score", payload.risk_score)
    if resolved_risk is not None:
        payload.risk_score = int(resolved_risk)
    resolved_action = str(decision.get("action") or payload.action)
    resolved_ar = decision.get("customer_message_ar", payload.customer_message_ar)
    resolved_en = decision.get("customer_message_en", payload.customer_message_en)
    resolved_location = decision.get("location_required", payload.location_required)
    resolved_upsell = decision.get("upsell_offer", payload.upsell_offer)
    resolved_note = decision.get("dashboard_note", payload.dashboard_note)
    if payload.risk_score is not None:
        order.risk_score = payload.risk_score
    if payload.gps_lat is not None and payload.gps_lng is not None:
        order.gps_lat, order.gps_lng = payload.gps_lat, payload.gps_lng

    # Keep the complete, auditable decision in the existing JSON column. This
    # avoids a destructive schema change and makes it immediately visible via
    # the existing dashboard OrderOut response.
    risk_reasons = dict(order.risk_reasons or {})
    risk_reasons["automation"] = {
        "action": resolved_action,
        "status": order.status.value,
        "location_required": resolved_location,
        "customer_message_ar": resolved_ar,
        "customer_message_en": resolved_en,
        "upsell_offer": resolved_upsell,
        "dashboard_note": resolved_note,
        "applied_at": datetime.now(UTC).isoformat(),
    }
    order.risk_reasons = risk_reasons
    order.llm_decision = {
        "action": resolved_action,
        "status": order.status.value,
        "location_required": resolved_location,
        "customer_message_ar": resolved_ar,
        "customer_message_en": resolved_en,
        "upsell_offer": resolved_upsell,
        "dashboard_note": resolved_note,
        "applied_at": datetime.now(UTC).isoformat(),
    }

    session.add(Message(
        order_id=order.id,
        store_id=order.store_id,
        type="llm_decision",
        direction="outbound",
        status="persisted",
    ))
    await session.flush()
    await sync_order_to_google_sheet(order, order.store_id, session)
    store_sync = await sync_order_to_store(order, "LLM_DECISION")
    await session.commit()
    await session.refresh(order)
    return {
        "status": "persisted",
        "order_id": str(order.id),
        "external_order_id": order.external_order_id,
        "order_status": order.status.value,
        "dashboard_updated": True,
        "store_sync": store_sync,
    }
