import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_session
from app.models import Order, OrderStatus, Store, Subscription, User
from app.schemas import OrderOut, RiskInput, RiskResult
from app.services.quota import FREE_PILOT_ORDER_LIMIT
from app.services.risk import calculate_risk

router = APIRouter(prefix="/api/orders", tags=["orders"])


async def owned_store(store_id: uuid.UUID, user: User, session: AsyncSession) -> Store:
    store = await session.scalar(select(Store).where(Store.id == store_id, Store.owner_id == user.id))
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    return store


@router.get("", response_model=list[OrderOut])
async def list_orders(
    store_id: uuid.UUID,
    status_filter: OrderStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await owned_store(store_id, user, session)
    statement = select(Order).where(Order.store_id == store_id).order_by(Order.created_at.desc()).limit(limit)
    if status_filter:
        statement = statement.where(Order.status == status_filter)
    return list((await session.scalars(statement)).all())


@router.get("/summary")
async def order_summary(
    store_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    from app.models import Integration, Platform
    await owned_store(store_id, user, session)
    rows = (
        await session.execute(
            select(Order.status, func.count(Order.id)).where(Order.store_id == store_id).group_by(Order.status)
        )
    ).all()
    counts = {status.value: count for status, count in rows}
    total = sum(counts.values())
    confirmed = counts.get(OrderStatus.confirmed.value, 0)
    subscription = await session.scalar(
        select(Subscription).where(Subscription.store_id == store_id)
    )
    plan = subscription.plan if subscription and subscription.status == "active" else "free"

    # Count GPS verified orders
    gps_verified = await session.scalar(
        select(func.count(Order.id)).where(
            Order.store_id == store_id,
            Order.gps_lat.is_not(None)
        )
    )

    # Calculate upsell counts scan
    all_orders = (await session.scalars(select(Order).where(Order.store_id == store_id))).all()
    upsell_count = 0
    upsell_revenue = 0.0
    for o in all_orders:
        has_upsell = False
        for item in (o.items or []):
            if isinstance(item, dict) and item.get("is_upsell"):
                has_upsell = True
                upsell_revenue += float(item.get("price") or item.get("amount") or 0)
        if has_upsell:
            upsell_count += 1

    # Check google sheets sync status
    sheets_integration = await session.scalar(
        select(Integration).where(
            Integration.store_id == store_id,
            Integration.platform == Platform.custom,
            Integration.external_store_id == "google_sheets"
        )
    )
    google_sheets_sync_healthy = bool(sheets_integration and sheets_integration.is_connected)

    return {
        "total": total,
        "confirmed": confirmed,
        "cancelled": counts.get(OrderStatus.cancelled.value, 0),
        "human_follow_up": counts.get(OrderStatus.human_follow_up.value, 0),
        "confirmation_rate": round((confirmed / total * 100), 1) if total else 0,
        "plan": plan,
        "pilot_orders_used": total if plan == "free" else None,
        "free_pilot_limit": FREE_PILOT_ORDER_LIMIT if plan == "free" else None,
        "free_pilot_remaining": max(FREE_PILOT_ORDER_LIMIT - total, 0) if plan == "free" else None,
        "gps_verified_count": gps_verified,
        "upsell_conversion_count": upsell_count,
        "upsell_revenue": upsell_revenue,
        "google_sheets_sync_healthy": google_sheets_sync_healthy,
    }


@router.post("/risk-preview", response_model=RiskResult)
async def risk_preview(payload: RiskInput, _: User = Depends(get_current_user)):
    return calculate_risk(payload)


from pydantic import BaseModel
class ChatbotActionInput(BaseModel):
    action: str # "confirm", "share_location", "accept_upsell", "reject_upsell"


@router.post("/simulate-chatbot")
async def simulate_chatbot_order(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    from app.models import Store, Customer, OrderStatus, RiskLevel
    store = await session.scalar(select(Store).where(Store.owner_id == user.id).limit(1))
    if not store:
        raise HTTPException(status_code=404, detail="Please register a store first")

    # Create customer if not exists
    from app.crypto import stable_hash
    customer_phone = "+966509999999"
    phone_hash = stable_hash(customer_phone)
    customer = await session.scalar(
        select(Customer).where(Customer.store_id == store.id, Customer.phone_hash == phone_hash)
    )
    if not customer:
        from app.crypto import encrypt_text
        customer = Customer(
            store_id=store.id,
            name_encrypted=encrypt_text("عميل تجريبي"),
            phone_encrypted=encrypt_text(customer_phone),
            phone_hash=phone_hash,
            total_orders=1
        )
        session.add(customer)
        await session.flush()
    else:
        customer.total_orders += 1

    import random
    from decimal import Decimal
    order_num = str(random.randint(1000, 9999))
    order = Order(
        store_id=store.id,
        customer_id=customer.id,
        external_order_id=f"sim-{order_num}",
        external_order_number=order_num,
        amount=Decimal("320.00"),
        currency="SAR",
        payment_method="cod",
        status=OrderStatus.pending,
        risk_score=15,
        risk_level=RiskLevel.low,
        items=[{"name": "طقم هدايا العيد الفاخر", "price": 320.0, "qty": 1}],
    )
    session.add(order)
    await session.commit()
    await session.refresh(order)
    return {"order_id": str(order.id), "external_order_number": order_num, "amount": "320.00"}


@router.post("/{order_id}/chatbot")
async def chatbot_action(
    order_id: uuid.UUID,
    payload: ChatbotActionInput,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    from decimal import Decimal
    from app.services.sheets import sync_order_to_google_sheet
    order = await session.scalar(
        select(Order).where(Order.id == order_id)
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    await owned_store(order.store_id, user, session)

    if payload.action == "confirm":
        order.status = OrderStatus.confirmed
    elif payload.action == "share_location":
        order.gps_lat = Decimal("24.7136")
        order.gps_lng = Decimal("46.6753")
        # Save mock text location coordinates in shipping address too
        from app.crypto import encrypt_text
        order.shipping_address_encrypted = encrypt_text("Riyadh GPS Verified: 24.7136, 46.6753")
    elif payload.action == "accept_upsell":
        current_items = list(order.items or [])
        current_items.append({
            "name": "عطر بريز الخليج (عرض خاص)",
            "price": 99.0,
            "is_upsell": True
        })
        order.items = current_items
        order.amount = order.amount + Decimal("99.0")
        # Sync immediately to Sheets on upsell accept
        await sync_order_to_google_sheet(order, order.store_id, session)
    elif payload.action == "reject_upsell":
        # Sync immediately to Sheets on upsell reject
        await sync_order_to_google_sheet(order, order.store_id, session)

    await session.commit()
    await session.refresh(order)
    return {
        "status": "success",
        "order_status": order.status.value,
        "gps_lat": str(order.gps_lat) if order.gps_lat else None,
        "gps_lng": str(order.gps_lng) if order.gps_lng else None,
        "amount": str(order.amount),
        "items": order.items
    }
