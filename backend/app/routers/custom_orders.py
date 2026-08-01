import hashlib
import secrets
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.crypto import encrypt_text, stable_hash
from app.database import get_session
from app.models import Customer, Order, Store, StoreApiKey, User
from app.schemas import (
    ApiKeyCreated,
    ApiKeyCreateInput,
    ApiKeyOut,
    CustomOrderInput,
    RiskInput,
)
from app.services.quota import enforce_order_allowance
from app.services.risk import calculate_risk

router = APIRouter(prefix="/api", tags=["custom-store-api"])

def key_hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


async def owned_store(store_id: uuid.UUID, user_id: uuid.UUID, session: AsyncSession) -> Store:
    store = await session.scalar(select(Store).where(Store.id == store_id, Store.owner_id == user_id))
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    return store


@router.post("/api-keys", response_model=ApiKeyCreated, status_code=201)
async def create_api_key(
    payload: ApiKeyCreateInput,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await owned_store(payload.store_id, user.id, session)
    secret = f"muj_live_{secrets.token_urlsafe(32)}"
    row = StoreApiKey(
        store_id=payload.store_id,
        name=payload.name.strip(),
        prefix=secret[:17],
        secret_hash=key_hash(secret),
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return ApiKeyCreated(
        id=row.id,
        name=row.name,
        prefix=row.prefix,
        created_at=row.created_at,
        last_used_at=row.last_used_at,
        api_key=secret,
    )


@router.get("/api-keys", response_model=list[ApiKeyOut])
async def list_api_keys(
    store_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await owned_store(store_id, user.id, session)
    rows = await session.scalars(
        select(StoreApiKey).where(
            StoreApiKey.store_id == store_id, StoreApiKey.revoked_at.is_(None)
        ).order_by(StoreApiKey.created_at.desc())
    )
    return list(rows.all())


@router.delete("/api-keys/{key_id}", status_code=204)
async def revoke_api_key(
    key_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    row = await session.scalar(
        select(StoreApiKey).join(Store).where(StoreApiKey.id == key_id, Store.owner_id == user.id)
    )
    if not row:
        raise HTTPException(status_code=404, detail="API key not found")
    row.revoked_at = datetime.now(UTC)
    await session.commit()


async def authenticate_api_key(raw_key: str, session: AsyncSession) -> StoreApiKey:
    row = await session.scalar(
        select(StoreApiKey).where(
            StoreApiKey.secret_hash == key_hash(raw_key), StoreApiKey.revoked_at.is_(None)
        )
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    row.last_used_at = datetime.now(UTC)
    return row


@router.post("/orders/custom", status_code=202)
async def receive_custom_order(
    payload: CustomOrderInput,
    x_mujeeb_api_key: str = Header(...),
    session: AsyncSession = Depends(get_session),
):
    api_key = await authenticate_api_key(x_mujeeb_api_key, session)
    existing = await session.scalar(
        select(Order).where(
            Order.store_id == api_key.store_id, Order.external_order_id == payload.order_id
        )
    )
    if existing:
        await session.commit()
        return {"status": "duplicate", "mujeeb_order_id": str(existing.id)}

    await enforce_order_allowance(api_key.store_id, session)

    phone_hash = stable_hash(payload.customer_phone)
    customer = await session.scalar(
        select(Customer).where(
            Customer.store_id == api_key.store_id, Customer.phone_hash == phone_hash
        )
    )
    is_new = customer is None
    if customer is None:
        customer = Customer(
            store_id=api_key.store_id,
            name_encrypted=encrypt_text(payload.customer_name),
            phone_encrypted=encrypt_text(payload.customer_phone),
            phone_hash=phone_hash,
            total_orders=1,
        )
        session.add(customer)
        await session.flush()
    else:
        customer.total_orders += 1

    risk = calculate_risk(RiskInput(
        is_new_customer=is_new,
        ordered_at_hour=datetime.now(UTC).hour,
        prior_store_rto_count=customer.rto_count,
        address_valid=bool(payload.shipping_city and payload.shipping_address),
        checkout_vpn_detected=payload.checkout_vpn_detected,
        amount=payload.amount,
    ))
    order = Order(
        store_id=api_key.store_id,
        customer_id=customer.id,
        external_order_id=payload.order_id,
        external_order_number=payload.order_number,
        amount=payload.amount,
        currency=payload.currency,
        payment_method=payload.payment_method.lower(),
        risk_score=risk.score,
        risk_level=risk.level,
        risk_reasons=risk.reasons,
        items=[item.model_dump(mode="json") for item in payload.items],
        shipping_city=payload.shipping_city,
        shipping_address_encrypted=(
            encrypt_text(payload.shipping_address) if payload.shipping_address else None
        ),
    )
    session.add(order)
    await session.commit()
    return {"status": "accepted", "mujeeb_order_id": str(order.id), "risk": risk.model_dump()}
