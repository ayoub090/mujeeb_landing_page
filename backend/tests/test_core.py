import hashlib
import hmac
import asyncio
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.models import RiskLevel
from app.models import Subscription, User
from fastapi import BackgroundTasks, HTTPException

from app.auth import is_internal_admin, require_internal_admin, require_superadmin
from app.config import get_settings
from app.routers import integrations
from app.routers.integrations import settings as integration_settings
from app.routers.integrations import (
    register_salla_webhooks,
    register_shopify_webhooks,
    register_zid_webhooks,
    salla_store_id,
    zid_store_id,
)
from app.routers.integrations import verify_shopify_callback
from app.routers.integrations import router as integrations_router
from app.routers.waapi import SendTestMessageInput, merchant_connection_status, qr_image_source
from app.routers.waapi import router as waapi_router
from app.routers import webhooks
from app.routers.webhooks import receive_salla, receive_shopify, receive_zid, signature_ok
from app.schemas import (
    BusinessLeadInput,
    CustomOrderInput,
    FunnelEventInput,
    MerchantTokenInput,
    RegisterInput,
    RiskInput,
    ShopifyStartInput,
)
from app.services.email import render_email
from app.services.quota import FREE_PILOT_ORDER_LIMIT, consume_confirmation_credit, enforce_order_allowance
from app.services.risk import calculate_risk
from app.models import FSMState
from app.services.fsm import InvalidTransition, transition
from app.services.address import ParsedAddress


def test_high_risk_order_is_explainable():
    result = calculate_risk(RiskInput(
        is_new_customer=True, ordered_at_hour=2, prior_store_rto_count=2,
        address_valid=False, checkout_vpn_detected=True, amount=1700,
    ))
    assert result.score == 100
    assert result.level == RiskLevel.high
    assert result.reasons["checkout_vpn"] > 0


def test_valid_gcc_phone_is_normalized():
    data = RegisterInput(
        email="owner@example.com", password="a-secure-password", full_name="Test Owner",
        phone="+966501234567", store_name="Store", country_code="SA",
    )
    assert data.phone == "+966501234567"


def test_non_gcc_phone_is_rejected():
    with pytest.raises(ValidationError):
        RegisterInput(
            email="owner@example.com", password="a-secure-password", full_name="Test Owner",
            phone="+33612345678", store_name="Store", country_code="SA",
        )


def test_webhook_signature_constant_time_contract():
    raw = b'{"event":"order.created"}'
    secret = "test-secret"
    signature = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    assert signature_ok(raw, signature, secret)
    assert not signature_ok(raw + b"x", signature, secret)


def test_custom_order_normalizes_customer_phone_and_currency():
    payload = CustomOrderInput(
        order_id="order-1",
        customer_name="Test Customer",
        customer_phone="+966501234567",
        amount=250,
        currency="sar",
    )
    assert payload.customer_phone == "+966501234567"
    assert payload.currency == "SAR"


def test_business_lead_normalizes_phone_and_requires_consent():
    payload = BusinessLeadInput(
        name="Merchant Owner",
        company="GCC Store",
        whatsapp="+212602689935",
        email="owner@example.com",
        platform="Shopify",
        monthly_orders="100_299",
        selected_plan="growth",
        contact_consent=True,
        consent_timestamp=datetime.now(UTC),
    )
    assert payload.whatsapp == "+212602689935"
    assert payload.platform == "shopify"
    assert payload.selected_plan == "growth"

    with pytest.raises(ValidationError):
        BusinessLeadInput(
            name="Merchant Owner",
            company="GCC Store",
            whatsapp="+212602689935",
            email="owner@example.com",
            platform="shopify",
            monthly_orders="100_299",
            contact_consent=False,
            consent_timestamp=datetime.now(UTC),
        )


def test_funnel_event_allowlist():
    event = FunnelEventInput(event_name="page_view", session_id="session-123", path="/")
    assert event.event_name == "page_view"
    with pytest.raises(ValidationError):
        FunnelEventInput(event_name="arbitrary_event", session_id="session-123", path="/")
    assert FunnelEventInput(
        event_name="pricing_select", session_id="session-123", path="/"
    ).event_name == "pricing_select"


def test_free_pilot_contract():
    assert FREE_PILOT_ORDER_LIMIT == 50
    assert Subscription.__table__.c.free_confirmations_remaining.default.arg == 50


class _SubscriptionSession:
    def __init__(self, subscription):
        self.subscription = subscription

    async def scalar(self, _query):
        return self.subscription


def test_confirmation_credit_is_consumed_only_on_success_and_blocks_at_zero():
    subscription = Subscription(plan="free", status="active", free_confirmations_remaining=1)
    session = _SubscriptionSession(subscription)
    assert asyncio.run(consume_confirmation_credit(subscription.store_id, session)) == 0
    assert subscription.free_confirmations_remaining == 0
    with pytest.raises(HTTPException) as raised:
        asyncio.run(enforce_order_allowance(subscription.store_id, session))
    assert raised.value.status_code == 402


def test_pricing_contract_matches_the_gcc_launch_offer():
    plans = {"starter": (99, 300), "growth": (249, 2000), "scale": (499, 5000)}
    assert plans["starter"] == (99, 300)
    assert plans["growth"] == (249, 2000)
    assert plans["scale"] == (499, 5000)


def test_shopify_domain_and_callback_hmac():
    normalized = ShopifyStartInput(
        store_id="d5c8f190-e39d-4e16-acf3-5c74025a0cc3", shop="gcc-brand"
    )
    assert normalized.shop == "gcc-brand.myshopify.com"
    params = {
        "code": "code-1",
        "shop": normalized.shop,
        "state": "state-1",
        "timestamp": "1785542400",
    }
    secret = "shopify-test-secret"
    integration_settings.shopify_client_secret = secret
    message = "&".join(f"{key}={value}" for key, value in sorted(params.items()))
    params["hmac"] = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
    assert verify_shopify_callback(params)
    params["code"] = "tampered"
    assert not verify_shopify_callback(params)


def test_merchant_connection_token_contract():
    payload = MerchantTokenInput(
        store_id="d5c8f190-e39d-4e16-acf3-5c74025a0cc3", token="merchant-connection-token"
    )
    assert payload.token == "merchant-connection-token"
    with pytest.raises(ValidationError):
        MerchantTokenInput(store_id="d5c8f190-e39d-4e16-acf3-5c74025a0cc3", token="short")


def test_custom_store_onboarding_route_is_available():
    assert any(route.path == "/api/integrations/custom/start" for route in integrations_router.routes)


def test_whatsapp_test_message_requires_only_store_id():
    payload = SendTestMessageInput(store_id="d5c8f190-e39d-4e16-acf3-5c74025a0cc3")
    assert str(payload.store_id) == "d5c8f190-e39d-4e16-acf3-5c74025a0cc3"


def test_waapi_status_route_is_available_for_onboarding():
    assert any(route.path == "/api/waapi/status" for route in waapi_router.routes)


def test_manual_waapi_connection_is_not_a_merchant_onboarding_route():
    route = next(route for route in waapi_router.routes if route.path == "/api/waapi/connect")
    assert route.methods == {"POST"}


def test_waapi_qr_is_returned_in_a_browser_safe_format():
    assert qr_image_source({"base64": "aGVsbG8="}) == "data:image/png;base64,aGVsbG8="
    assert qr_image_source({"qr": "https://provider.example/qr.png"}) == "https://provider.example/qr.png"
    assert qr_image_source({"data": {"qr": "data:image/png;base64,abc"}}) == "data:image/png;base64,abc"


def test_merchant_whatsapp_status_never_exposes_provider_secrets():
    connection = type("Connection", (), {"status": "ready", "instance_id": "12345"})()
    payload = merchant_connection_status(connection, "+966501234567")
    assert payload == {
        "configured": True,
        "connected": True,
        "display_phone": "+966501234567",
        "status": "ready",
    }
    assert not {"instance_id", "provider", "token", "webhook"} & payload.keys()


def test_operational_email_templates_are_transactional():
    subject, plain, html = render_email("pilot_40", {"store": "GCC Store", "remaining": 10})
    assert "10" in plain
    assert "GCC Store" in html
    assert "تقرير" in subject


def test_cod_fsm_guardrails():
    assert transition(FSMState.awaiting_confirmation, FSMState.awaiting_address_choice, "confirm").target == FSMState.awaiting_address_choice
    with pytest.raises(InvalidTransition):
        transition(FSMState.awaiting_confirmation, FSMState.order_confirmed, "skip_address")


def test_address_contract_requires_city_and_district():
    parsed = ParsedAddress(is_valid=False, formatted_address="Riyadh")
    assert parsed.is_valid is False


def test_internal_admin_is_opt_in_by_configured_email():
    settings = get_settings()
    original = settings.internal_admin_email
    staff = User(email="staff@usemujeeb.com", password_hash="x", full_name="Staff")
    try:
        settings.internal_admin_email = "staff@usemujeeb.com"
        assert is_internal_admin(staff)
        settings.internal_admin_email = ""
        assert not is_internal_admin(staff)
    finally:
        settings.internal_admin_email = original


def test_non_admin_cannot_run_internal_simulations():
    settings = get_settings()
    original = settings.internal_admin_email
    merchant = User(email="merchant@example.com", password_hash="x", full_name="Merchant")
    try:
        settings.internal_admin_email = "staff@usemujeeb.com"
        with pytest.raises(HTTPException) as raised:
            require_internal_admin(merchant)
        assert raised.value.status_code == 403
    finally:
        settings.internal_admin_email = original


def test_superadmin_dependency_rejects_non_admin_accounts():
    settings = get_settings()
    original = settings.internal_admin_email
    merchant = User(email="merchant@example.com", password_hash="x", full_name="Merchant")
    try:
        settings.internal_admin_email = "staff@usemujeeb.com"
        with pytest.raises(HTTPException) as raised:
            asyncio.run(require_superadmin(merchant))
        assert raised.value.status_code == 403
    finally:
        settings.internal_admin_email = original


class _WebhookRequest:
    def __init__(self, raw: bytes):
        self.raw = raw

    async def body(self):
        return self.raw


class _WebhookSession:
    def __init__(self):
        self.events = []
        self.commits = 0

    async def scalar(self, _query):
        return None

    def add(self, event):
        self.events.append(event)

    async def flush(self):
        return None

    async def commit(self):
        self.commits += 1


def test_store_webhooks_acknowledge_before_background_processing():
    original = (
        webhooks.settings.salla_webhook_secret,
        webhooks.settings.zid_webhook_secret,
        webhooks.settings.shopify_client_secret,
    )
    try:
        webhooks.settings.salla_webhook_secret = "salla-secret"
        webhooks.settings.zid_webhook_secret = "zid-secret"
        webhooks.settings.shopify_client_secret = "shopify-secret"

        salla_raw = b'{"event":"order.created"}'
        salla_tasks = BackgroundTasks()
        salla_result = asyncio.run(receive_salla(
            _WebhookRequest(salla_raw), salla_tasks,
            hmac.new(b"salla-secret", salla_raw, hashlib.sha256).hexdigest(), None,
            _WebhookSession(),
        ))
        assert salla_result == {"received": True, "queued": True}
        assert len(salla_tasks.tasks) == 1

        zid_raw = b'{"event":"order.create"}'
        zid_tasks = BackgroundTasks()
        zid_result = asyncio.run(receive_zid(
            _WebhookRequest(zid_raw), zid_tasks, "Basic " + __import__("base64").b64encode(b"mujeeb:zid-secret").decode(), _WebhookSession(),
        ))
        assert zid_result == {"received": True, "queued": True}
        assert len(zid_tasks.tasks) == 1

        shopify_raw = b'{"id":123}'
        shopify_signature = __import__("base64").b64encode(
            hmac.new(b"shopify-secret", shopify_raw, hashlib.sha256).digest()
        ).decode()
        shopify_tasks = BackgroundTasks()
        shopify_result = asyncio.run(receive_shopify(
            _WebhookRequest(shopify_raw), shopify_tasks, shopify_signature,
            "store.myshopify.com", "orders/create", "event-1", _WebhookSession(),
        ))
        assert shopify_result == {"received": True, "queued": True}
        assert len(shopify_tasks.tasks) == 1
    finally:
        (
            webhooks.settings.salla_webhook_secret,
            webhooks.settings.zid_webhook_secret,
            webhooks.settings.shopify_client_secret,
        ) = original


class _WebhookResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {"data": {"webhookSubscriptionCreate": {"userErrors": []}}}


class _WebhookClient:
    calls: list[dict] = []

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def post(self, url, **kwargs):
        self.calls.append({"url": url, **kwargs})
        return _WebhookResponse()


class _StoreInfoResponse:
    is_error = False

    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload


class _StoreInfoClient:
    payload: dict = {}

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def get(self, url, **kwargs):
        return _StoreInfoResponse(self.payload)


def test_salla_merchant_token_registers_order_webhooks(monkeypatch):
    original_secret = integration_settings.salla_webhook_secret
    original_base_url = integration_settings.app_base_url
    try:
        _WebhookClient.calls = []
        integration_settings.salla_webhook_secret = "salla-secret"
        integration_settings.app_base_url = "https://api.example.test"
        monkeypatch.setattr(integrations.httpx, "AsyncClient", _WebhookClient)
        asyncio.run(register_salla_webhooks("merchant-token"))
        assert [call["json"]["event"] for call in _WebhookClient.calls] == ["order.created", "order.status.updated"]
        assert all(call["json"]["url"] == "https://api.example.test/api/webhooks/salla" for call in _WebhookClient.calls)
    finally:
        integration_settings.salla_webhook_secret = original_secret
        integration_settings.app_base_url = original_base_url


def test_zid_merchant_token_registers_order_webhooks(monkeypatch):
    original_secret = integration_settings.zid_webhook_secret
    original_base_url = integration_settings.app_base_url
    try:
        _WebhookClient.calls = []
        integration_settings.zid_webhook_secret = "zid-secret"
        integration_settings.app_base_url = "https://api.example.test"
        monkeypatch.setattr(integrations.httpx, "AsyncClient", _WebhookClient)
        asyncio.run(register_zid_webhooks({"access_token": "merchant-token"}))
        assert [call["json"]["event"] for call in _WebhookClient.calls] == ["order.create", "order.status.update"]
        assert all(call["json"]["target_url"] == "https://api.example.test/api/webhooks/zid" for call in _WebhookClient.calls)
    finally:
        integration_settings.zid_webhook_secret = original_secret
        integration_settings.app_base_url = original_base_url


def test_shopify_webhooks_use_current_graphql_input_shape(monkeypatch):
    original_base_url = integration_settings.app_base_url
    try:
        _WebhookClient.calls = []
        integration_settings.app_base_url = "https://api.example.test"
        monkeypatch.setattr(integrations.httpx, "AsyncClient", _WebhookClient)
        asyncio.run(register_shopify_webhooks("store.myshopify.com", "shop-token"))
        assert len(_WebhookClient.calls) == 6
        first = _WebhookClient.calls[0]["json"]
        assert "$webhookSubscription: WebhookSubscriptionInput!" in first["query"]
        assert first["variables"]["webhookSubscription"] == {
            "uri": "https://api.example.test/api/webhooks/shopify"
        }
    finally:
        integration_settings.app_base_url = original_base_url


def test_personal_store_keys_resolve_the_external_store_for_webhook_routing(monkeypatch):
    monkeypatch.setattr(integrations.httpx, "AsyncClient", _StoreInfoClient)
    _StoreInfoClient.payload = {"data": {"id": 1305146709}}
    assert asyncio.run(salla_store_id("merchant-token")) == "1305146709"
    _StoreInfoClient.payload = {"store": {"uuid": "zid-store-42"}}
    assert asyncio.run(zid_store_id("merchant-token")) == "zid-store-42"
