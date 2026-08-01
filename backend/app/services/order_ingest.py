import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crypto import encrypt_text, stable_hash
from app.models import Customer, Order, Store, User
from app.schemas import RiskInput
from app.services.lifecycle import enqueue_email, record_lifecycle_event
from app.services.quota import enforce_order_allowance
from app.services.risk import calculate_risk


async def ingest_order(
    session: AsyncSession,
    *,
    store_id: uuid.UUID,
    source: str,
    external_order_id: str,
    external_order_number: str | None,
    customer_name: str,
    customer_phone: str,
    amount: Decimal,
    currency: str,
    payment_method: str,
    items: list,
    shipping_city: str | None = None,
    shipping_address: str | None = None,
) -> tuple[Order, bool]:
    existing = await session.scalar(select(Order).where(
        Order.store_id == store_id, Order.external_order_id == external_order_id
    ))
    if existing:
        return existing, False
    await enforce_order_allowance(store_id, session)
    phone_hash = stable_hash(customer_phone)
    customer = await session.scalar(select(Customer).where(
        Customer.store_id == store_id, Customer.phone_hash == phone_hash
    ))
    is_new = customer is None
    if customer is None:
        customer = Customer(
            store_id=store_id,
            name_encrypted=encrypt_text(customer_name),
            phone_encrypted=encrypt_text(customer_phone),
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
        address_valid=bool(shipping_city or shipping_address),
        checkout_vpn_detected=False,
        amount=amount,
    ))
    order = Order(
        store_id=store_id,
        customer_id=customer.id,
        external_order_id=external_order_id,
        external_order_number=external_order_number,
        amount=amount,
        currency=currency.upper(),
        payment_method=payment_method.lower(),
        risk_score=risk.score,
        risk_level=risk.level,
        risk_reasons=risk.reasons,
        items=items,
        shipping_city=shipping_city,
        shipping_address_encrypted=encrypt_text(shipping_address) if shipping_address else None,
    )
    session.add(order)
    await session.flush()
    await record_lifecycle_event(
        session, "order_received", store_id=store_id,
        properties={"source": source, "risk_level": risk.level.value},
    )
    count = await session.scalar(select(func.count(Order.id)).where(Order.store_id == store_id))
    if count == 40:
        store = await session.get(Store, store_id)
        owner = await session.get(User, store.owner_id) if store else None
        if store and owner:
            await enqueue_email(
                session, dedupe_key=f"pilot-40:{store.id}", kind="pilot_40",
                recipient=owner.email,
                payload={"name": owner.full_name, "store": store.name, "remaining": 10},
            )
    return order, True
