"""Internal, non-production Salla seed used to record the Mujeeb product demos.

The module never calls Salla and never delivers a WhatsApp message. It creates
the same local store, integration, webhook audit event and pending order state
that the real Salla pipeline consumes, which makes it safe for video capture.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from copy import deepcopy
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_superadmin
from app.crypto import encrypt_text
from app.database import get_session
from app.models import FSMConversation, Integration, Platform, Store, Subscription, User, WebhookEvent
from app.services.fsm import initial_state
from app.services.order_ingest import ingest_order


router = APIRouter(prefix="/api/admin/demo/salla", tags=["internal-demo"])

DEMO_STORE_NAME = "متجر أصالة للعود"
DEMO_STORE_NAME_EN = "Asala Oud & Perfumes"
DEMO_COUNTRY = "المملكة العربية السعودية"
DEMO_EXTERNAL_STORE_ID = "asala-oud-riyadh-demo"
# Explicitly synthetic: never used against Salla and never exposed in full.
DEMO_MERCHANT_API_KEY = "salla_demo_sec_99482710482019482"


def demo_salla_order_payload() -> dict:
    """Return a fresh, realistic Saudi COD order payload for a local demo."""
    return {
        "event": "order.created",
        "merchant": DEMO_EXTERNAL_STORE_ID,
        "data": {
            "id": 10482,
            "reference_id": "ORD-2026-10482",
            "currency": "SAR",
            "total": {"amount": 380, "currency": "SAR"},
            "payment_method": "cod",
            "status": {"id": 1, "name": "بانتظار التأكيد (Pending Confirmation)"},
            "customer": {
                "first_name": "عبدالله",
                "last_name": "الشمري",
                "mobile": "+966550000000",
                "email": "demo.customer@asala.example",
                "city": "الرياض",
                "district": "حي النرجس",
            },
            "items": [
                {"name": "عطر مروكي ملكي فاخر 100 مل", "quantity": 1, "price": 380}
            ],
        },
    }


class DemoDispatchInput(BaseModel):
    store_id: uuid.UUID


async def _owned_demo_store(store_id: uuid.UUID, user: User, session: AsyncSession) -> Store:
    store = await session.scalar(
        select(Store).where(Store.id == store_id, Store.owner_id == user.id, Store.platform == Platform.salla)
    )
    if not store:
        raise HTTPException(status_code=404, detail="Demo Salla store not found")
    integration = await session.scalar(
        select(Integration).where(
            Integration.store_id == store.id,
            Integration.platform == Platform.salla,
            Integration.external_store_id == DEMO_EXTERNAL_STORE_ID,
        )
    )
    if not integration:
        raise HTTPException(status_code=409, detail="Store is not the Asala Salla demo")
    return store


@router.get("/profile")
async def profile(_: User = Depends(require_superadmin)):
    """Fixture details, available only in the internal recording workspace."""
    return {
        "demo_only": True,
        "name": DEMO_STORE_NAME,
        "name_en": DEMO_STORE_NAME_EN,
        "currency": "SAR",
        "country": DEMO_COUNTRY,
        "merchant_api_key_hint": "salla_demo_sec_••••19482",
        "webhook_payload": demo_salla_order_payload(),
    }


@router.post("/seed")
async def seed_demo_store(
    user: User = Depends(require_superadmin),
    session: AsyncSession = Depends(get_session),
):
    """Create or return the SuperAdmin-owned Asala video sandbox."""
    store = await session.scalar(
        select(Store).where(
            Store.owner_id == user.id,
            Store.name == DEMO_STORE_NAME,
            Store.platform == Platform.salla,
        )
    )
    created = store is None
    if store is None:
        store = Store(owner_id=user.id, name=DEMO_STORE_NAME, platform=Platform.salla, currency="SAR", country_code="SA")
        session.add(store)
        await session.flush()

    integration = await session.scalar(
        select(Integration).where(Integration.store_id == store.id, Integration.platform == Platform.salla)
    )
    if integration is None:
        session.add(Integration(
            store_id=store.id,
            platform=Platform.salla,
            external_store_id=DEMO_EXTERNAL_STORE_ID,
            access_token_encrypted=encrypt_text(DEMO_MERCHANT_API_KEY),
            refresh_token_encrypted=None,
            auxiliary_token_encrypted=None,
            is_connected=True,
        ))
    else:
        integration.external_store_id = DEMO_EXTERNAL_STORE_ID
        integration.access_token_encrypted = encrypt_text(DEMO_MERCHANT_API_KEY)
        integration.is_connected = True

    subscription = await session.scalar(select(Subscription).where(Subscription.store_id == store.id))
    if subscription is None:
        session.add(Subscription(store_id=store.id, plan="free", status="active", free_confirmations_remaining=50))

    await session.commit()
    return {
        "created": created,
        "store_id": str(store.id),
        "store_name": store.name,
        "platform": "salla",
        "currency": "SAR",
        "country": DEMO_COUNTRY,
        "webhook_ready": True,
    }


@router.post("/dispatch")
async def dispatch_demo_order(
    payload: DemoDispatchInput,
    user: User = Depends(require_superadmin),
    session: AsyncSession = Depends(get_session),
):
    """Dispatch the seed order into Mujeeb without external delivery."""
    store = await _owned_demo_store(payload.store_id, user, session)
    event_payload = deepcopy(demo_salla_order_payload())
    raw = json.dumps(event_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    event_key = f"salla-demo:{store.id}:10482"
    event = await session.scalar(
        select(WebhookEvent).where(WebhookEvent.provider == "salla-demo", WebhookEvent.event_key == event_key)
    )
    if event is None:
        event = WebhookEvent(
            provider="salla-demo", event_key=event_key, event_type="order.created",
            payload_hash=hashlib.sha256(raw).hexdigest(), payload=event_payload, status="received",
        )
        session.add(event)

    data = event_payload["data"]
    customer = data["customer"]
    customer_name = f"{customer['first_name']} {customer['last_name']}"
    order, created = await ingest_order(
        session,
        store_id=store.id,
        source="salla-demo",
        external_order_id=str(data["id"]),
        external_order_number=data["reference_id"],
        customer_name=customer_name,
        customer_phone=customer["mobile"],
        amount=Decimal(str(data["total"]["amount"])),
        currency=data["currency"],
        payment_method=data["payment_method"],
        items=data["items"],
        shipping_city=customer["city"],
        shipping_address=customer["district"],
    )
    conversation = await session.scalar(select(FSMConversation).where(FSMConversation.order_id == order.id))
    if conversation is None:
        session.add(FSMConversation(
            order_id=order.id,
            phone_number=customer["mobile"],
            current_state=initial_state(),
            session_data={"demo": True, "channel": "salla", "delivery": "suppressed"},
        ))
    event.status = "processed"
    await session.commit()
    return {
        "received": True,
        "created": created,
        "store_id": str(store.id),
        "order_id": str(order.id),
        "order_number": data["reference_id"],
        "status": "pending_confirmation",
        "whatsapp_delivery": "suppressed_for_demo",
        "next_step": "Use the internal dashboard to record the confirmation journey.",
    }
