import hashlib
import hmac
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.models import RiskLevel
from app.routers.webhooks import signature_ok
from app.schemas import (
    BusinessLeadInput,
    CustomOrderInput,
    FunnelEventInput,
    RegisterInput,
    RiskInput,
)
from app.services.risk import calculate_risk


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
        contact_consent=True,
        consent_timestamp=datetime.now(UTC),
    )
    assert payload.whatsapp == "+212602689935"
    assert payload.platform == "shopify"

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
