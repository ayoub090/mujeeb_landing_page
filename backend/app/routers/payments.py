import hashlib
import hmac
import json
import uuid

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.config import get_settings
from app.database import get_session
from app.models import Store, Subscription, User, WebhookEvent
from app.schemas import CheckoutInput, UrlOut

router = APIRouter(prefix="/api/payments", tags=["payments"])
settings = get_settings()


@router.post("/checkout", response_model=UrlOut)
async def create_checkout(
    payload: CheckoutInput,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    store = await session.scalar(
        select(Store).where(Store.id == payload.store_id, Store.owner_id == user.id)
    )
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    products = {
        "starter": settings.creem_product_starter,
        "growth": settings.creem_product_growth,
        "scale": settings.creem_product_scale,
    }
    product_id = products.get(payload.plan)
    if not settings.creem_api_key or not product_id:
        raise HTTPException(status_code=503, detail="This billing plan is not configured")
    body = {
        "product_id": product_id,
        "success_url": f"{settings.frontend_origin}/dashboard/billing?checkout=success",
        "metadata": {"store_id": str(store.id), "plan": payload.plan},
        "customer": {"email": user.email},
    }
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            f"{settings.creem_api_base}/v1/checkouts",
            headers={"x-api-key": settings.creem_api_key, "Content-Type": "application/json"},
            json=body,
        )
    if response.is_error:
        raise HTTPException(status_code=502, detail="Unable to create the secure checkout")
    checkout_url = response.json().get("checkout_url")
    if not checkout_url:
        raise HTTPException(status_code=502, detail="Billing provider returned no checkout URL")
    return UrlOut(url=checkout_url)


@router.post("/webhooks/creem")
async def creem_webhook(
    request: Request,
    creem_signature: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
):
    raw = await request.body()
    if not settings.creem_webhook_secret or not creem_signature:
        raise HTTPException(status_code=401, detail="Missing webhook signature")
    expected = hmac.new(settings.creem_webhook_secret.encode(), raw, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, creem_signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    try:
        event = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON") from exc

    event_key = str(event.get("id") or hashlib.sha256(raw).hexdigest())
    if await session.scalar(
        select(WebhookEvent.id).where(
            WebhookEvent.provider == "creem", WebhookEvent.event_key == event_key
        )
    ):
        return {"received": True, "duplicate": True}
    event_type = event.get("eventType")
    record = WebhookEvent(
        provider="creem",
        event_key=event_key,
        payload_hash=hashlib.sha256(raw).hexdigest(),
        event_type=event_type,
        payload=event,
    )
    session.add(record)

    obj = event.get("object") or {}
    metadata = obj.get("metadata") or {}
    store_id = metadata.get("store_id")
    if store_id:
        try:
            parsed_store_id = uuid.UUID(store_id)
        except ValueError:
            parsed_store_id = None
        subscription = await session.scalar(
            select(Subscription).where(Subscription.store_id == parsed_store_id)
        ) if parsed_store_id else None
        if subscription:
            if event_type in {"subscription.paid", "checkout.completed"}:
                subscription.plan = metadata.get("plan", subscription.plan)
                subscription.status = "active"
                subscription.creem_subscription_id = obj.get("id") or subscription.creem_subscription_id
                subscription.creem_customer_id = (obj.get("customer") or {}).get("id") or subscription.creem_customer_id
            elif event_type in {"subscription.canceled", "subscription.expired", "subscription.paused"}:
                subscription.status = "inactive"
            record.status = "processed"
    await session.commit()
    return {"received": True}
