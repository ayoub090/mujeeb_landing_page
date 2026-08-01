from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, verify_password
from app.config import get_settings
from app.crypto import decrypt_text, stable_hash
from app.database import get_session
from app.models import (
    Customer,
    DataDeletionRequest,
    Integration,
    Order,
    Store,
    Subscription,
    User,
    WhatsAppAccount,
)
from app.schemas import DataDeletionInput
from app.services.lifecycle import enqueue_email, record_lifecycle_event

router = APIRouter(prefix="/api/privacy", tags=["privacy"])


@router.get("/export")
async def export_account_data(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    stores = list((await session.scalars(select(Store).where(Store.owner_id == user.id))).all())
    store_ids = [store.id for store in stores]
    customers = list((await session.scalars(
        select(Customer).where(Customer.store_id.in_(store_ids))
    )).all()) if store_ids else []
    orders = list((await session.scalars(
        select(Order).where(Order.store_id.in_(store_ids)).order_by(Order.created_at)
    )).all()) if store_ids else []
    integrations = list((await session.scalars(
        select(Integration).where(Integration.store_id.in_(store_ids))
    )).all()) if store_ids else []
    whatsapp = list((await session.scalars(
        select(WhatsAppAccount).where(WhatsAppAccount.store_id.in_(store_ids))
    )).all()) if store_ids else []
    subscriptions = list((await session.scalars(
        select(Subscription).where(Subscription.store_id.in_(store_ids))
    )).all()) if store_ids else []
    payload = {
        "generated_at": datetime.now(UTC),
        "account": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "phone": decrypt_text(user.phone_encrypted) if user.phone_encrypted else None,
            "created_at": user.created_at,
        },
        "stores": [{
            "id": row.id, "name": row.name, "platform": row.platform.value,
            "country_code": row.country_code, "currency": row.currency, "created_at": row.created_at,
        } for row in stores],
        "customers": [{
            "id": row.id, "store_id": row.store_id,
            "name": decrypt_text(row.name_encrypted) if row.name_encrypted else None,
            "phone": decrypt_text(row.phone_encrypted), "total_orders": row.total_orders,
            "rto_count": row.rto_count, "marketing_opt_in_at": row.marketing_opt_in_at,
        } for row in customers],
        "orders": [{
            "id": row.id, "store_id": row.store_id, "external_order_id": row.external_order_id,
            "external_order_number": row.external_order_number, "amount": row.amount,
            "currency": row.currency, "status": row.status.value, "risk_score": row.risk_score,
            "risk_reasons": row.risk_reasons, "items": row.items, "shipping_city": row.shipping_city,
            "shipping_address": decrypt_text(row.shipping_address_encrypted) if row.shipping_address_encrypted else None,
            "created_at": row.created_at,
        } for row in orders],
        "integrations": [{
            "platform": row.platform.value, "external_store_id": row.external_store_id,
            "is_connected": row.is_connected, "created_at": row.created_at,
        } for row in integrations],
        "whatsapp_accounts": [{
            "waba_id": row.waba_id, "phone_number_id": row.phone_number_id,
            "display_phone": decrypt_text(row.display_phone_encrypted) if row.display_phone_encrypted else None,
            "status": row.status, "created_at": row.created_at,
        } for row in whatsapp],
        "subscriptions": [{
            "plan": row.plan, "status": row.status,
            "orders_count_this_month": row.orders_count_this_month, "trial_ends_at": row.trial_ends_at,
        } for row in subscriptions],
    }
    return jsonable_encoder(payload)


@router.post("/deletion-request", status_code=202)
async def schedule_deletion(
    payload: DataDeletionInput,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Password confirmation failed")
    existing = await session.scalar(select(DataDeletionRequest).where(
        DataDeletionRequest.user_id == user.id, DataDeletionRequest.status == "scheduled"
    ))
    if existing:
        return {"status": existing.status, "scheduled_for": existing.scheduled_for}
    scheduled_for = datetime.now(UTC) + timedelta(days=get_settings().privacy_deletion_grace_days)
    request = DataDeletionRequest(
        user_id=user.id, email_hash=stable_hash(user.email), scheduled_for=scheduled_for
    )
    session.add(request)
    await session.flush()
    await record_lifecycle_event(session, "deletion_scheduled", user_id=user.id)
    await enqueue_email(
        session, dedupe_key=f"deletion-scheduled:{request.id}", kind="deletion_scheduled",
        recipient=user.email, payload={"name": user.full_name},
    )
    await session.commit()
    return {"status": "scheduled", "scheduled_for": scheduled_for}


@router.get("/deletion-request")
async def deletion_status(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    request = await session.scalar(
        select(DataDeletionRequest).where(DataDeletionRequest.user_id == user.id)
        .order_by(DataDeletionRequest.created_at.desc())
    )
    if not request:
        return {"status": "none"}
    return {
        "status": request.status, "scheduled_for": request.scheduled_for,
        "cancelled_at": request.cancelled_at, "completed_at": request.completed_at,
    }


@router.delete("/deletion-request", status_code=204)
async def cancel_deletion(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    request = await session.scalar(select(DataDeletionRequest).where(
        DataDeletionRequest.user_id == user.id, DataDeletionRequest.status == "scheduled"
    ))
    if not request:
        raise HTTPException(status_code=404, detail="No scheduled deletion request")
    request.status = "cancelled"
    request.cancelled_at = datetime.now(UTC)
    await session.commit()
