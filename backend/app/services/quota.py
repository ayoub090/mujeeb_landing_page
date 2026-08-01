import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Order, Subscription

FREE_PILOT_ORDER_LIMIT = 50


async def enforce_order_allowance(store_id: uuid.UUID, session: AsyncSession) -> None:
    subscription = await session.scalar(
        select(Subscription)
        .where(Subscription.store_id == store_id)
        .with_for_update()
    )
    if subscription and subscription.status == "active" and subscription.plan != "free":
        return

    pilot_orders_used = await session.scalar(
        select(func.count(Order.id)).where(Order.store_id == store_id)
    )
    if (pilot_orders_used or 0) >= FREE_PILOT_ORDER_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "code": "free_pilot_limit_reached",
                "message": "The 50-order free pilot is complete. Activate a plan to continue.",
                "limit": FREE_PILOT_ORDER_LIMIT,
            },
        )
