import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_session
from app.models import Order, OrderStatus, Store, Subscription, User
from app.schemas import OrderOut, RiskInput, RiskResult
from app.services.quota import FREE_PILOT_ORDER_LIMIT, utc_month_start
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
    await owned_store(store_id, user, session)
    rows = (
        await session.execute(
            select(Order.status, func.count(Order.id)).where(Order.store_id == store_id).group_by(Order.status)
        )
    ).all()
    counts = {status.value: count for status, count in rows}
    total = sum(counts.values())
    confirmed = counts.get(OrderStatus.confirmed.value, 0)
    monthly_total = await session.scalar(
        select(func.count(Order.id)).where(
            Order.store_id == store_id, Order.created_at >= utc_month_start()
        )
    ) or 0
    subscription = await session.scalar(
        select(Subscription).where(Subscription.store_id == store_id)
    )
    plan = subscription.plan if subscription and subscription.status == "active" else "free"
    return {
        "total": total,
        "confirmed": confirmed,
        "cancelled": counts.get(OrderStatus.cancelled.value, 0),
        "human_follow_up": counts.get(OrderStatus.human_follow_up.value, 0),
        "confirmation_rate": round((confirmed / total * 100), 1) if total else 0,
        "plan": plan,
        "orders_this_month": monthly_total,
        "free_pilot_limit": FREE_PILOT_ORDER_LIMIT if plan == "free" else None,
        "free_pilot_remaining": max(FREE_PILOT_ORDER_LIMIT - monthly_total, 0)
        if plan == "free" else None,
    }


@router.post("/risk-preview", response_model=RiskResult)
async def risk_preview(payload: RiskInput, _: User = Depends(get_current_user)):
    return calculate_risk(payload)
