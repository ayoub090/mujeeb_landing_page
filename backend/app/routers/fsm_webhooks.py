from __future__ import annotations

import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import FSMConversation, FSMState, Order, OrderStatus
from app.services.address import parse_manual_address, reverse_geocode
from app.services.fsm import initial_state, transition
from app.services.order_ingest import ingest_order
from app.services.store_sync import sync_order_to_store
from app.services.whatsapp import confirmation_payload, send_whatsapp_message

router = APIRouter(prefix="/api/v1", tags=["fsm"])


def _value(payload: dict, *keys: str, default=None):
    for key in keys:
        value = payload.get(key)
        if value is not None:
            return value
    return default


@router.post("/webhooks/order-created", status_code=202)
async def order_created(payload: dict, session: AsyncSession = Depends(get_session)):
    try:
        store_id = uuid.UUID(str(_value(payload, "store_id", "merchant_id")))
    except (ValueError, TypeError):
        raise HTTPException(status_code=422, detail="store_id is required")
    customer = payload.get("customer") or {}
    shipping = payload.get("shipping_address") or payload.get("shipping") or {}
    phone = _value(payload, "customer_phone", default=_value(customer, "phone", "mobile"))
    if not phone:
        raise HTTPException(status_code=422, detail="customer_phone is required")
    order, created = await ingest_order(
        session, store_id=store_id, source=str(payload.get("source") or "custom"),
        external_order_id=str(_value(payload, "order_id", "external_order_id")),
        external_order_number=str(_value(payload, "order_number", "external_order_number", default="")) or None,
        customer_name=str(_value(payload, "customer_name", default=_value(customer, "name", default="Customer"))),
        customer_phone=str(phone), amount=Decimal(str(_value(payload, "total_amount", "amount", default=0))),
        currency=str(payload.get("currency") or "SAR"), payment_method=str(payload.get("payment_method") or "cod"),
        items=payload.get("items") or [], shipping_city=shipping.get("city"),
        shipping_address=shipping.get("address") or shipping.get("street"),
    )
    conversation = await session.scalar(select(FSMConversation).where(
        FSMConversation.phone_number == str(phone), FSMConversation.order_id == order.id
    ))
    if conversation is None:
        conversation = FSMConversation(phone_number=str(phone), order_id=order.id, current_state=initial_state(), session_data={})
        session.add(conversation)
    else:
        conversation.current_state = initial_state()
    await session.commit()
    message = await send_whatsapp_message(str(phone), confirmation_payload(order.external_order_number or str(order.id), str(order.amount), str(_value(payload, "customer_name", default="Customer"))))
    return {"received": True, "created": created, "order_id": str(order.id), "state": conversation.current_state.value, "whatsapp": message}


@router.post("/webhooks/logistics-update", status_code=202)
async def logistics_update(payload: dict, session: AsyncSession = Depends(get_session)):
    order = await session.scalar(select(Order).where(
        Order.external_order_id == str(_value(payload, "order_id", "external_order_id", default=""))
    ))
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    status = str(payload.get("status") or "").upper()
    order.tracking_number = payload.get("tracking_number") or order.tracking_number
    order.carrier_name = payload.get("carrier_name") or payload.get("carrier") or order.carrier_name
    order.status = {"DELIVERED": OrderStatus.delivered, "OUT_FOR_DELIVERY": OrderStatus.shipped}.get(status, order.status)
    conversation = await session.scalar(select(FSMConversation).where(FSMConversation.order_id == order.id))
    if conversation:
        conversation.current_state = FSMState.tracking_active
        conversation.session_data = {**conversation.session_data, "tracking_status": status, "tracking_link": payload.get("tracking_url")}
    await session.commit()
    return {"updated": True, "order_id": str(order.id), "status": status, "tracking_url": payload.get("tracking_url")}


@router.post("/webhooks/whatsapp/messages", status_code=202)
async def whatsapp_message(request: Request, session: AsyncSession = Depends(get_session), x_store_id: str | None = Header(default=None)):
    body = await request.json()
    messages = body.get("messages") or body.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [])
    processed = 0
    for message in messages:
        phone = str(message.get("from") or "")
        conversation = await session.scalar(select(FSMConversation).where(FSMConversation.phone_number == phone).order_by(FSMConversation.updated_at.desc()))
        if not conversation:
            continue
        order = await session.get(Order, conversation.order_id)
        if not order:
            continue
        msg_type = message.get("type")
        if msg_type == "location":
            location = message["location"]
            address = await reverse_geocode(float(location["latitude"]), float(location["longitude"]))
            conversation.current_state = transition(conversation.current_state, FSMState.confirm_address_text, "location").target
            order.gps_lat, order.gps_lng = Decimal(str(location["latitude"])), Decimal(str(location["longitude"]))
            order.address_data = address.model_dump()
        elif msg_type == "text":
            text = message.get("text", {}).get("body", "")
            if text.lower() in {"confirm", "confirm_order", "yes"} and conversation.current_state == FSMState.awaiting_confirmation:
                conversation.current_state = FSMState.awaiting_address_choice
            elif text.lower() in {"cancel", "cancel_order", "no"}:
                conversation.current_state = FSMState.order_cancelled
                order.status = OrderStatus.cancelled
            elif conversation.current_state == FSMState.awaiting_address_choice:
                address = await parse_manual_address(text)
                conversation.current_state = transition(conversation.current_state, FSMState.confirm_address_text, "manual_address").target
                order.address_data = address.model_dump()
            elif conversation.current_state == FSMState.confirm_address_text and text.lower() in {"yes", "correct", "نعم", "نعم صحيح"}:
                conversation.current_state = FSMState.upsell_pitch
                order.upsell_status = "offered"
            elif conversation.current_state == FSMState.upsell_pitch and text.lower() in {"no", "no thanks", "لا"}:
                conversation.current_state = transition(conversation.current_state, FSMState.final_store_sync, "upsell_declined").target
                order.upsell_status = "declined"
                order.status = OrderStatus.confirmed
                await sync_order_to_store(order, "FINAL_STORE_SYNC")
                conversation.current_state = FSMState.order_confirmed
        elif msg_type == "interactive":
            action = message.get("interactive", {}).get("button_reply", {}).get("id")
            if action == "confirm_order" and conversation.current_state == FSMState.awaiting_confirmation:
                conversation.current_state = FSMState.awaiting_address_choice
            elif action == "cancel_order":
                conversation.current_state = FSMState.order_cancelled
                order.status = OrderStatus.cancelled
                await sync_order_to_store(order, "ORDER_CANCELLED")
            elif action == "confirm_address" and conversation.current_state == FSMState.confirm_address_text:
                conversation.current_state = FSMState.upsell_pitch
                order.upsell_status = "offered"
            elif action == "change_address" and conversation.current_state == FSMState.confirm_address_text:
                conversation.current_state = FSMState.awaiting_address_choice
            elif action in {"reject_upsell", "complete_order"} and conversation.current_state == FSMState.upsell_pitch:
                conversation.current_state = FSMState.final_store_sync
                order.upsell_status = "declined"
                order.status = OrderStatus.confirmed
                await sync_order_to_store(order, "FINAL_STORE_SYNC")
                conversation.current_state = FSMState.order_confirmed
            elif action == "accept_upsell" and conversation.current_state == FSMState.upsell_pitch:
                order.items = [*(order.items or []), {"name": "GCC accessory upsell", "quantity": 1, "price": 99, "is_upsell": True}]
                order.amount += Decimal("99")
                order.upsell_status = "accepted"
                conversation.current_state = FSMState.final_store_sync
                order.status = OrderStatus.confirmed
                await sync_order_to_store(order, "FINAL_STORE_SYNC")
                conversation.current_state = FSMState.order_confirmed
        processed += 1
    await session.commit()
    return {"processed": processed}
