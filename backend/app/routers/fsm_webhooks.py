from __future__ import annotations

import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.crypto import encrypt_text
from app.database import get_session
from app.models import FSMConversation, FSMState, Order, OrderStatus
from app.services.address import parse_manual_address, reverse_geocode
from app.services.fsm import ALLOWED_TRANSITIONS, transition
from app.services.confirmation import start_cod_confirmation
from app.services.order_ingest import ingest_order
from app.services.quota import consume_confirmation_credit
from app.services.store_sync import sync_order_to_store
from app.services.whatsapp import (
    address_choice_payload,
    address_confirmation_payload,
    confirmation_payload,
    send_whatsapp_message,
    tracking_payload,
    upsell_payload,
)

router = APIRouter(prefix="/api/v1", tags=["fsm"])


def _value(payload: dict, *keys: str, default=None):
    for key in keys:
        value = payload.get(key)
        if value is not None:
            return value
    return default


def _can_cancel(state: FSMState) -> bool:
    return FSMState.order_cancelled in ALLOWED_TRANSITIONS.get(state, set())


async def _final_sync(conversation: FSMConversation, order: Order, event: str) -> None:
    result = await sync_order_to_store(order, event)
    conversation.session_data = {**conversation.session_data, "store_sync": result}


async def _mark_order_confirmed(order: Order, session: AsyncSession) -> None:
    """Set a confirmed order once and consume a free credit exactly once."""
    if order.status != OrderStatus.confirmed:
        await consume_confirmation_credit(order.store_id, session)
        order.status = OrderStatus.confirmed


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
        session,
        store_id=store_id,
        source=str(payload.get("source") or "custom"),
        external_order_id=str(_value(payload, "order_id", "external_order_id")),
        external_order_number=str(_value(payload, "order_number", "external_order_number", default="")) or None,
        customer_name=str(_value(payload, "customer_name", default=_value(customer, "name", default="Customer"))),
        customer_phone=str(phone),
        amount=Decimal(str(_value(payload, "total_amount", "amount", default=0))),
        currency=str(payload.get("currency") or "SAR"),
        payment_method=str(payload.get("payment_method") or "cod"),
        items=payload.get("items") or [],
        shipping_city=shipping.get("city"),
        shipping_address=shipping.get("address") or shipping.get("street"),
    )
    message = await start_cod_confirmation(
        session, order, str(phone), str(_value(payload, "customer_name", default="Customer"))
    )
    # Start the n8n/OpenRouter branch as soon as the order is accepted. The
    # adapter is optional in local/mock mode and reports that it is disabled
    # when no webhook URL is configured.
    automation = await sync_order_to_store(order, "ORDER_CREATED")
    await session.commit()
    state = await session.scalar(select(FSMConversation.current_state).where(FSMConversation.order_id == order.id))
    return {"received": True, "created": created, "order_id": str(order.id), "state": state.value if state else None, "whatsapp": message, "automation": automation}


@router.post("/webhooks/logistics-update", status_code=202)
async def logistics_update(payload: dict, session: AsyncSession = Depends(get_session)):
    order = await session.scalar(
        select(Order).where(
            Order.external_order_id == str(_value(payload, "order_id", "external_order_id", default=""))
        )
    )
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
        await send_whatsapp_message(conversation.phone_number, tracking_payload(status, payload.get("tracking_url")))
    await session.commit()
    return {"updated": True, "order_id": str(order.id), "status": status, "tracking_url": payload.get("tracking_url")}


@router.post("/webhooks/whatsapp/messages", status_code=202)
async def whatsapp_message(
    request: Request,
    session: AsyncSession = Depends(get_session),
    x_store_id: str | None = Header(default=None),
):
    del x_store_id  # store routing is resolved from the persisted phone/order session.
    body = await request.json()
    messages = body.get("messages") or body.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [])
    processed = 0
    for message in messages:
        phone = str(message.get("from") or "")
        conversation = await session.scalar(
            select(FSMConversation).where(FSMConversation.phone_number == phone).order_by(FSMConversation.updated_at.desc())
        )
        if not conversation:
            continue
        order = await session.get(Order, conversation.order_id)
        if not order:
            continue
        msg_type = message.get("type")
        if msg_type == "location" and conversation.current_state == FSMState.awaiting_address_choice:
            location = message["location"]
            conversation.current_state = transition(conversation.current_state, FSMState.reverse_geo, "location_received").target
            address = await reverse_geocode(float(location["latitude"]), float(location["longitude"]))
            conversation.current_state = transition(conversation.current_state, FSMState.confirm_address_text, "reverse_geocoded").target
            order.gps_lat, order.gps_lng = Decimal(str(location["latitude"])), Decimal(str(location["longitude"]))
            order.address_data = address.model_dump()
            # Keep the verified location in the canonical shipping fields as
            # well as the audit JSON. Store adapters (Salla/Shopify/custom)
            # can therefore write the same address without re-parsing GPS.
            order.shipping_city = address.city or address.district or order.shipping_city
            if address.formatted_address:
                order.shipping_address_encrypted = encrypt_text(address.formatted_address)
            fallback = f"{float(location['latitude']):.6f}, {float(location['longitude']):.6f}"
            order.llm_decision = {"type": "address_resolution", "method": "reverse_geocode", "provider": "google_maps" if address.formatted_address != fallback else "fallback", "valid": address.is_valid, "missing": address.missing}
            await send_whatsapp_message(phone, address_confirmation_payload(order.address_data))
        elif msg_type == "text":
            text = str(message.get("text", {}).get("body", "")).strip()
            lowered = text.lower()
            if conversation.current_state == FSMState.modify_variants:
                conversation.session_data = {**conversation.session_data, "variant_request": text}
                conversation.current_state = transition(conversation.current_state, FSMState.awaiting_confirmation, "variant_updated").target
                await send_whatsapp_message(phone, confirmation_payload(order.external_order_number or str(order.id), str(order.amount), "there"))
            elif lowered in {"confirm", "confirm_order", "yes"} and conversation.current_state == FSMState.awaiting_confirmation:
                conversation.current_state = transition(conversation.current_state, FSMState.awaiting_address_choice, "confirm").target
                await send_whatsapp_message(phone, address_choice_payload())
            elif lowered in {"cancel", "cancel_order", "no"} and _can_cancel(conversation.current_state):
                conversation.current_state = transition(conversation.current_state, FSMState.order_cancelled, "cancel").target
                order.status = OrderStatus.cancelled
                await _final_sync(conversation, order, "ORDER_CANCELLED")
            elif lowered in {"where is my order", "tracking", "order tracking", "في طلب"} and conversation.current_state in {FSMState.order_confirmed, FSMState.tracking_active}:
                conversation.current_state = FSMState.tracking_active
                conversation.session_data = {**conversation.session_data, "tracking_requested": True}
                await send_whatsapp_message(phone, tracking_payload(conversation.session_data.get("tracking_status", "in transit"), conversation.session_data.get("tracking_link")))
            elif conversation.current_state == FSMState.awaiting_address_choice:
                conversation.current_state = transition(conversation.current_state, FSMState.llm_parser_strict, "manual_address").target
                address = await parse_manual_address(text)
                conversation.current_state = transition(conversation.current_state, FSMState.confirm_address_text, "parsed_address").target
                order.address_data = address.model_dump()
                order.shipping_city = address.city or address.district or order.shipping_city
                if address.formatted_address:
                    order.shipping_address_encrypted = encrypt_text(address.formatted_address)
                settings = get_settings()
                order.llm_decision = {"type": "address_resolution", "method": "manual_parser", "provider": "openrouter" if settings.openrouter_api_key else "fallback", "model": settings.openrouter_model if settings.openrouter_api_key else None, "valid": address.is_valid, "missing": address.missing}
                await send_whatsapp_message(phone, address_confirmation_payload(order.address_data))
            elif conversation.current_state == FSMState.confirm_address_text and lowered in {"yes", "correct", "confirm address"}:
                conversation.current_state = transition(conversation.current_state, FSMState.upsell_pitch, "address_confirmed").target
                order.upsell_status = "offered"
                await send_whatsapp_message(phone, upsell_payload())
            elif conversation.current_state == FSMState.upsell_pitch and lowered in {"no", "no thanks", "complete order"}:
                conversation.current_state = transition(conversation.current_state, FSMState.final_store_sync, "upsell_declined").target
                order.upsell_status = "declined"
                await _mark_order_confirmed(order, session)
                await _final_sync(conversation, order, "FINAL_STORE_SYNC")
                conversation.current_state = transition(conversation.current_state, FSMState.order_confirmed, "store_sync_complete").target
        elif msg_type == "interactive":
            action = message.get("interactive", {}).get("button_reply", {}).get("id")
            if action == "confirm_order" and conversation.current_state == FSMState.awaiting_confirmation:
                conversation.current_state = transition(conversation.current_state, FSMState.awaiting_address_choice, "confirm").target
                await send_whatsapp_message(phone, address_choice_payload())
            elif action == "cancel_order" and _can_cancel(conversation.current_state):
                conversation.current_state = transition(conversation.current_state, FSMState.order_cancelled, "cancel").target
                order.status = OrderStatus.cancelled
                await _final_sync(conversation, order, "ORDER_CANCELLED")
            elif action == "modify_order" and conversation.current_state == FSMState.awaiting_confirmation:
                conversation.current_state = transition(conversation.current_state, FSMState.modify_variants, "modify").target
                await send_whatsapp_message(phone, {"type": "text", "text": {"body": "Which item variant should we change (size, color, or quantity)?"}})
            elif action == "send_location" and conversation.current_state == FSMState.awaiting_address_choice:
                await send_whatsapp_message(phone, {"type": "text", "text": {"body": "Please share your WhatsApp location pin to verify delivery."}})
            elif action == "type_address" and conversation.current_state == FSMState.awaiting_address_choice:
                await send_whatsapp_message(phone, {"type": "text", "text": {"body": "Please type your city, district, and street."}})
            elif action == "confirm_address" and conversation.current_state == FSMState.confirm_address_text:
                conversation.current_state = transition(conversation.current_state, FSMState.upsell_pitch, "address_confirmed").target
                order.upsell_status = "offered"
                await send_whatsapp_message(phone, upsell_payload())
            elif action == "change_address" and conversation.current_state == FSMState.confirm_address_text:
                conversation.current_state = transition(conversation.current_state, FSMState.awaiting_address_choice, "change_address").target
                await send_whatsapp_message(phone, address_choice_payload())
            elif action in {"reject_upsell", "complete_order"} and conversation.current_state == FSMState.upsell_pitch:
                conversation.current_state = transition(conversation.current_state, FSMState.final_store_sync, "upsell_declined").target
                order.upsell_status = "declined"
                await _mark_order_confirmed(order, session)
                await _final_sync(conversation, order, "FINAL_STORE_SYNC")
                conversation.current_state = transition(conversation.current_state, FSMState.order_confirmed, "store_sync_complete").target
            elif action == "accept_upsell" and conversation.current_state == FSMState.upsell_pitch:
                order.items = [*(order.items or []), {"name": "GCC accessory upsell", "quantity": 1, "price": 99, "is_upsell": True}]
                order.amount += Decimal("99")
                order.upsell_status = "accepted"
                conversation.current_state = transition(conversation.current_state, FSMState.final_store_sync, "upsell_accepted").target
                await _mark_order_confirmed(order, session)
                await _final_sync(conversation, order, "FINAL_STORE_SYNC")
                conversation.current_state = transition(conversation.current_state, FSMState.order_confirmed, "store_sync_complete").target
        processed += 1
    await session.commit()
    return {"processed": processed}
