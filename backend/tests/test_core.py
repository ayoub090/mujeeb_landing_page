import hashlib
import hmac
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.models import RiskLevel
from app.routers.integrations import settings as integration_settings
from app.routers.integrations import verify_shopify_callback
from app.routers.webhooks import signature_ok
from app.schemas import (
    BusinessLeadInput,
    CustomOrderInput,
    FunnelEventInput,
    RegisterInput,
    RiskInput,
    ShopifyStartInput,
)
from app.services.email import render_email
from app.services.quota import FREE_PILOT_ORDER_LIMIT
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
