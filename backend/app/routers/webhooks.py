import base64
import hashlib
import hmac
import json
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import SessionLocal, get_session
from app.crypto import stable_hash
from app.models import Customer, FSMConversation, Integration, Order, OrderStatus, Platform, Store, WebhookEvent
from app.services.order_ingest import ingest_order
from app.services.confirmation import start_cod_confirmation

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])
settings = get_settings()


def signature_ok(raw: bytes, received: str | None, secret: str, prefix: str = "") -> bool:
    if not received or not secret:
        return False
    digest = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"{prefix}{digest}", received)


async def persist_event(provider: str, raw: bytes, payload: dict, session: AsyncSession) -> WebhookEvent | None:
    event_type = str(payload.get("event") or payload.get("eventType") or payload.get("topic") or "unknown")
    supplied_id = payload.get("id") or payload.get("event_id") or payload.get("webhook_id")
    event_key = str(supplied_id or hashlib.sha256(raw).hexdigest())
    exists = await session.scalar(
        select(WebhookEvent.id).where(
            WebhookEvent.provider == provider, WebhookEvent.event_key == event_key
        )
    )
    if exists:
        return None
    event = WebhookEvent(
        provider=provider, event_key=event_key, payload_hash=hashlib.sha256(raw).hexdigest(),
        event_type=event_type, payload=payload, status="received",
    )
    session.add(event)
    await session.flush()
    return event


def _decimal(value: object) -> Decimal:
    if isinstance(value, dict):
        value = value.get("amount") or value.get("value") or 0
    try:
        return Decimal(str(value or 0))
    except InvalidOperation:
        return Decimal(0)


async def integration_store_id(
    session: AsyncSession, platform: Platform, external_store_id: object
):
    # Providers are inconsistent here: Salla can send the merchant as an
    # object while Zid/Shopify normally send a scalar identifier. Normalise
    # before looking up the integration so an incoming order always stays
    # isolated to the merchant that connected it.
    if isinstance(external_store_id, dict):
        external_store_id = (
            external_store_id.get("id")
            or external_store_id.get("store_id")
            or external_store_id.get("uuid")
        )
    if external_store_id in (None, ""):
        return None
    return await session.scalar(select(Integration.store_id).where(
        Integration.platform == platform,
        Integration.external_store_id == str(external_store_id),
        Integration.is_connected.is_(True),
    ))


def _status_value(value: object) -> str:
    if isinstance(value, dict):
        return str(value.get("slug") or value.get("name") or value.get("status") or "").lower()
    return str(value or "").lower()


def _map_external_status(value: object) -> OrderStatus | None:
    status = _status_value(value)
    if any(token in status for token in ("cancel", "canceled", "cancelled")):
        return OrderStatus.cancelled
    if "deliver" in status or status in {"delivered", "completed"}:
        return OrderStatus.delivered
    if "return" in status or "refund" in status:
        return OrderStatus.returned
    if "ship" in status or "fulfill" in status:
        return OrderStatus.shipped
    return None


async def update_order_status(
    session: AsyncSession,
    *,
    store_id,
    external_order_id: object,
    external_status: object,
) -> None:
    mapped = _map_external_status(external_status)
    if not mapped or external_order_id in (None, ""):
        return
    order = await session.scalar(select(Order).where(
        Order.store_id == store_id,
        Order.external_order_id == str(external_order_id),
    ))
    if order:
        order.status = mapped


async def _process_salla(payload: dict, session: AsyncSession) -> None:
    event = str(payload.get("event") or payload.get("type") or "")
    if event == "order.created":
        store_id = await integration_store_id(session, Platform.salla, payload.get("merchant"))
        data = payload.get("data") or {}
        customer = data.get("customer") or {}
        address = data.get("shipping") or data.get("shipping_address") or {}
        phone = customer.get("mobile") or customer.get("phone") or address.get("mobile") or address.get("phone")
        if store_id and phone:
            order, created_order = await ingest_order(
                session, store_id=store_id, source="salla", external_order_id=str(data.get("id")),
                external_order_number=str(data.get("reference_id") or data.get("number") or data.get("id")),
                customer_name=str(customer.get("name") or "Customer"), customer_phone=str(phone),
                amount=_decimal(data.get("total")), currency=str(data.get("currency") or "SAR"),
                payment_method=str((data.get("payment_method") or {}).get("name") if isinstance(data.get("payment_method"), dict) else data.get("payment_method") or "cod"),
                items=data.get("items") or [], shipping_city=str(address.get("city") or "") or None,
                shipping_address=str(address.get("address") or address.get("street") or "") or None,
            )
            if created_order:
                await start_cod_confirmation(session, order, str(phone), str(customer.get("name") or "Customer"))
    elif event in {"order.status.updated", "order.updated", "order.cancelled"}:
        data = payload.get("data") or payload.get("order") or {}
        store_id = await integration_store_id(session, Platform.salla, payload.get("merchant"))
        await update_order_status(session, store_id=store_id, external_order_id=data.get("id") or data.get("order_id"), external_status=data.get("status") or data.get("order_status") or event)


async def _process_zid(payload: dict, session: AsyncSession) -> None:
    event = payload.get("event") or payload.get("type")
    if event != "order.create":
        return
    data = payload.get("data") or payload.get("order") or payload
    store_id = await integration_store_id(session, Platform.zid, payload.get("store_id") or data.get("store_id"))
    customer = data.get("customer") or {}
    address = data.get("shipping_address") or data.get("shipping") or {}
    phone = customer.get("mobile") or customer.get("phone") or address.get("phone")
    if store_id and phone:
        order, created_order = await ingest_order(
            session, store_id=store_id, source="zid", external_order_id=str(data.get("id")),
            external_order_number=str(data.get("code") or data.get("order_number") or data.get("id")),
            customer_name=str(customer.get("name") or "Customer"), customer_phone=str(phone),
            amount=_decimal(data.get("total") or data.get("total_price")), currency=str(data.get("currency") or "SAR"),
            payment_method=str(data.get("payment_method") or "cod"), items=data.get("products") or data.get("items") or [],
            shipping_city=str(address.get("city") or "") or None,
            shipping_address=str(address.get("address") or address.get("street") or "") or None,
        )
        if created_order:
            await start_cod_confirmation(session, order, str(phone), str(customer.get("name") or "Customer"))


async def _process_shopify(payload: dict, session: AsyncSession) -> None:
    topic = payload.get("topic")
    shop = payload.get("_shop_domain")
    if topic in {"orders/create", "orders/updated"}:
        store_id = await integration_store_id(session, Platform.shopify, shop)
        customer = payload.get("customer") or {}
        address = payload.get("shipping_address") or payload.get("billing_address") or {}
        phone = address.get("phone") or customer.get("phone")
        if store_id and phone:
            customer_name = " ".join(filter(None, [customer.get("first_name"), customer.get("last_name")])) or "Customer"
            order, created_order = await ingest_order(
                session, store_id=store_id, source="shopify", external_order_id=str(payload.get("id")),
                external_order_number=str(payload.get("name") or payload.get("order_number") or payload.get("id")),
                customer_name=customer_name, customer_phone=str(phone), amount=_decimal(payload.get("total_price")),
                currency=str(payload.get("currency") or "SAR"),
                payment_method="cod" if any("cash" in str(name).lower() for name in payload.get("payment_gateway_names") or []) else "online",
                items=payload.get("line_items") or [], shipping_city=str(address.get("city") or "") or None,
                shipping_address=" ".join(filter(None, [address.get("address1"), address.get("address2")])) or None,
            )
            if created_order:
                await start_cod_confirmation(session, order, str(phone), customer_name)
        if topic == "orders/updated":
            await update_order_status(session, store_id=store_id, external_order_id=payload.get("id"), external_status="cancelled" if payload.get("cancelled_at") else (payload.get("fulfillment_status") or payload.get("financial_status")))
    elif topic == "customers/data_request":
        # The verified request is retained as an auditable work item. Mujeeb's
        # privacy operator can export the referenced orders to the merchant;
        # Shopify allows up to 30 days to complete the request.
        return
    elif topic == "customers/redact":
        integration = await session.scalar(select(Integration).where(
            Integration.platform == Platform.shopify,
            Integration.external_store_id == shop,
        ))
        if not integration:
            return
        requested_ids = {str(value) for value in payload.get("orders_to_redact") or []}
        customer_payload = payload.get("customer") or {}
        phone = customer_payload.get("phone")
        order_rows = []
        if requested_ids:
            order_rows = list((await session.scalars(select(Order).where(
                Order.store_id == integration.store_id,
                Order.external_order_id.in_(requested_ids),
            ))).all())
        customer_ids = {order.customer_id for order in order_rows}
        if phone:
            phone_customer = await session.scalar(select(Customer).where(
                Customer.store_id == integration.store_id,
                Customer.phone_hash == stable_hash(str(phone)),
            ))
            if phone_customer:
                customer_ids.add(phone_customer.id)
        for order in order_rows:
            order.shipping_city = None
            order.shipping_address_encrypted = None
            order.gps_lat = None
            order.gps_lng = None
            order.address_data = {}
            order.llm_decision = {}
        if customer_ids:
            conversations = (await session.scalars(select(FSMConversation).join(
                Order, FSMConversation.order_id == Order.id
            ).where(Order.customer_id.in_(customer_ids)))).all()
            for conversation in conversations:
                conversation.phone_number = f"redacted-{str(conversation.id)[:8]}"
                conversation.session_data = {}
            customers = (await session.scalars(select(Customer).where(Customer.id.in_(customer_ids)))).all()
            for customer in customers:
                customer.name_encrypted = None
                customer.phone_encrypted = ""
                customer.phone_hash = stable_hash(f"redacted:{customer.id}")
                customer.marketing_opt_in_at = None
        # Do not preserve the incoming phone/email in the audit payload after
        # fulfilling a redaction request.
        payload["customer"] = {"id": customer_payload.get("id")}
    elif topic == "shop/redact":
        integration = await session.scalar(select(Integration).where(
            Integration.platform == Platform.shopify,
            Integration.external_store_id == shop,
        ))
        if integration:
            store = await session.get(Store, integration.store_id)
            if store:
                await session.delete(store)
    elif topic == "app/uninstalled":
        integration = await session.scalar(select(Integration).where(Integration.platform == Platform.shopify, Integration.external_store_id == shop))
        if integration:
            integration.is_connected = False


async def process_saved_webhook(event_id) -> None:
    """Process persisted store webhooks after their HTTP acknowledgement."""
    async with SessionLocal() as session:
        event = await session.get(WebhookEvent, event_id)
        if not event or event.status == "processed":
            return
        try:
            if event.provider == "salla":
                await _process_salla(event.payload, session)
            elif event.provider == "zid":
                await _process_zid(event.payload, session)
            elif event.provider == "shopify":
                await _process_shopify(event.payload, session)
            event.status = "processed"
        except Exception as exc:  # retain an auditable failure without retrying the store webhook
            event.status = f"failed:{type(exc).__name__}"[:32]
        await session.commit()


@router.get("/meta", response_class=PlainTextResponse)
async def verify_meta(
    mode: str = Query(alias="hub.mode"),
    token: str = Query(alias="hub.verify_token"),
    challenge: str = Query(alias="hub.challenge"),
):
    if mode != "subscribe" or not hmac.compare_digest(token, settings.meta_webhook_verify_token):
        raise HTTPException(status_code=403, detail="Webhook verification failed")
    return challenge


@router.post("/meta")
async def receive_meta(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
):
    raw = await request.body()
    if not signature_ok(raw, x_hub_signature_256, settings.meta_app_secret, "sha256="):
        raise HTTPException(status_code=401, detail="Invalid Meta signature")
    payload = json.loads(raw)
    event = await persist_event("meta", raw, payload, session)
    created = event is not None
    await session.commit()
    # Meta delivers inbound WhatsApp messages nested under entry/changes. Feed
    # the same persisted FSM handler used by the test/custom webhook route so
    # signature validation, deduplication, and state transitions stay aligned.
    messages = payload.get("messages") or payload.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [])
    fsm_result = {"processed": 0}
    if messages and created:
        from app.routers.fsm_webhooks import whatsapp_message

        class _MetaRequest:
            async def json(self):
                return {"messages": messages}

        fsm_result = await whatsapp_message(_MetaRequest(), session=session)
    return {"received": True, "duplicate": not created, "fsm": fsm_result}


@router.post("/salla")
async def receive_salla(
    request: Request,
    background_tasks: BackgroundTasks,
    x_salla_signature: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
):
    raw = await request.body()
    candidate = x_salla_signature or (authorization.removeprefix("Bearer ") if authorization else None)
    if not signature_ok(raw, candidate, settings.salla_webhook_secret):
        raise HTTPException(status_code=401, detail="Invalid Salla signature")
    payload = json.loads(raw)
    event_record = await persist_event("salla", raw, payload, session)
    await session.commit()
    if event_record:
        background_tasks.add_task(process_saved_webhook, event_record.id)
    return {"received": True, "queued": event_record is not None}


@router.post("/zid")
async def receive_zid(
    request: Request,
    background_tasks: BackgroundTasks,
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
):
    raw = await request.body()
    expected_basic = "Basic " + base64.b64encode(
        f"mujeeb:{settings.zid_webhook_secret}".encode()
    ).decode()
    if not authorization or not settings.zid_webhook_secret or not hmac.compare_digest(authorization, expected_basic):
        raise HTTPException(status_code=401, detail="Invalid Zid signature")
    payload = json.loads(raw)
    event_record = await persist_event("zid", raw, payload, session)
    await session.commit()
    if event_record:
        background_tasks.add_task(process_saved_webhook, event_record.id)
    return {"received": True, "queued": event_record is not None}


@router.post("/shopify")
async def receive_shopify(
    request: Request,
    background_tasks: BackgroundTasks,
    x_shopify_hmac_sha256: str | None = Header(default=None),
    x_shopify_shop_domain: str | None = Header(default=None),
    x_shopify_topic: str | None = Header(default=None),
    x_shopify_webhook_id: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
):
    raw = await request.body()
    expected = base64.b64encode(
        hmac.new(settings.shopify_client_secret.encode(), raw, hashlib.sha256).digest()
    ).decode()
    if not x_shopify_hmac_sha256 or not settings.shopify_client_secret or not hmac.compare_digest(
        expected, x_shopify_hmac_sha256
    ):
        raise HTTPException(status_code=401, detail="Invalid Shopify signature")
    payload = json.loads(raw)
    payload["topic"] = x_shopify_topic or "unknown"
    payload["_shop_domain"] = x_shopify_shop_domain
    if x_shopify_webhook_id:
        payload["webhook_id"] = x_shopify_webhook_id
    event_record = await persist_event("shopify", raw, payload, session)
    await session.commit()
    if event_record:
        background_tasks.add_task(process_saved_webhook, event_record.id)
    return {"received": True, "queued": event_record is not None}
