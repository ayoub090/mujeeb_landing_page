import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Subscription

FREE_PILOT_ORDER_LIMIT = 50


async def enforce_order_allowance(store_id: uuid.UUID, session: AsyncSession) -> None:
    subscription = await session.scalar(
        select(Subscription)
        .where(Subscription.store_id == store_id)
        .with_for_update()
    )
    if subscription and subscription.status == "active" and subscription.plan != "free":
        return

    remaining = subscription.free_confirmations_remaining if subscription else FREE_PILOT_ORDER_LIMIT
    if remaining <= 0:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "code": "free_pilot_limit_reached",
                "message": "The 50-order free pilot is complete. Activate a plan to continue.",
                "limit": FREE_PILOT_ORDER_LIMIT,
            },
        )


async def consume_confirmation_credit(store_id: uuid.UUID, session: AsyncSession) -> int | None:
    """Atomically consume one free confirmation after a customer confirms.

    This is intentionally separate from order intake: a cancelled or ignored
    order never consumes a pilot credit. The row lock keeps concurrent WhatsApp
    replies from spending the same final credit twice.
    """
    subscription = await session.scalar(
        select(Subscription)
        .where(Subscription.store_id == store_id)
        .with_for_update()
    )
    if subscription and subscription.status == "active" and subscription.plan != "free":
        return None
    if not subscription or subscription.free_confirmations_remaining <= 0:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "code": "free_pilot_limit_reached",
                "message": "The 50-order free pilot is complete. Activate a plan to continue.",
                "limit": FREE_PILOT_ORDER_LIMIT,
            },
        )
    subscription.free_confirmations_remaining -= 1
    return subscription.free_confirmations_remaining
