import uuid
from datetime import datetime
from decimal import Decimal

import phonenumbers
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.models import OrderStatus, Platform, RiskLevel


class RegisterInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    full_name: str = Field(min_length=2, max_length=160)
    phone: str = Field(min_length=8, max_length=32)
    store_name: str = Field(min_length=2, max_length=160)
    platform: Platform = Platform.custom
    country_code: str = Field(default="SA", min_length=2, max_length=2)

    @field_validator("country_code")
    @classmethod
    def gcc_country(cls, value: str) -> str:
        normalized = value.upper()
        if normalized not in {"SA", "AE", "KW", "BH", "QA", "OM"}:
            raise ValueError("country_code must be a GCC country")
        return normalized

    @field_validator("phone")
    @classmethod
    def valid_phone(cls, value: str) -> str:
        try:
            parsed = phonenumbers.parse(value, None)
        except phonenumbers.NumberParseException as exc:
            raise ValueError("Use an international phone number, for example +9665…") from exc
        if not phonenumbers.is_valid_number(parsed):
            raise ValueError("Invalid phone number")
        if phonenumbers.region_code_for_number(parsed) not in {"SA", "AE", "KW", "BH", "QA", "OM"}:
            raise ValueError("Phone number must be from a GCC country")
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)


class LoginInput(BaseModel):
    email: EmailStr
    password: str


class StoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    platform: Platform
    currency: str
    country_code: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    email: EmailStr
    full_name: str
    stores: list[StoreOut] = []
    is_internal_admin: bool = False


class RiskInput(BaseModel):
    is_new_customer: bool = True
    ordered_at_hour: int = Field(ge=0, le=23)
    prior_store_rto_count: int = Field(default=0, ge=0)
    address_valid: bool = True
    checkout_vpn_detected: bool = False
    amount: Decimal = Field(default=0, ge=0)


class RiskResult(BaseModel):
    score: int
    level: RiskLevel
    reasons: dict[str, int]


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    external_order_number: str | None
    customer_name: str | None = None
    amount: Decimal
    currency: str
    status: OrderStatus
    risk_score: int
    risk_level: RiskLevel
    risk_reasons: dict
    gps_lat: Decimal | None = None
    gps_lng: Decimal | None = None
    items: list = []
    created_at: datetime


class GoogleSheetsConnectInput(BaseModel):
    store_id: uuid.UUID
    url: str = Field(min_length=10)


class EmbeddedSignupInput(BaseModel):
    store_id: uuid.UUID
    code: str = Field(min_length=8)
    waba_id: str = Field(min_length=2, max_length=128)
    phone_number_id: str = Field(min_length=2, max_length=128)


class CheckoutInput(BaseModel):
    store_id: uuid.UUID
    plan: str


class OAuthStartInput(BaseModel):
    store_id: uuid.UUID


class MerchantTokenInput(OAuthStartInput):
    token: str = Field(min_length=8, max_length=2048)


class ShopifyStartInput(OAuthStartInput):
    shop: str = Field(min_length=3, max_length=120)

    @field_validator("shop")
    @classmethod
    def valid_shop_domain(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized.endswith(".myshopify.com"):
            normalized = normalized.removesuffix(".myshopify.com")
        if not normalized.replace("-", "").isalnum() or normalized.startswith("-") or normalized.endswith("-"):
            raise ValueError("Use the shop name or its .myshopify.com domain")
        return f"{normalized}.myshopify.com"


class UrlOut(BaseModel):
    url: str


class ApiKeyCreateInput(BaseModel):
    store_id: uuid.UUID
    name: str = Field(default="Default", min_length=2, max_length=80)


class ApiKeyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    prefix: str
    created_at: datetime
    last_used_at: datetime | None


class ApiKeyCreated(ApiKeyOut):
    api_key: str


class CustomOrderItem(BaseModel):
    name: str = Field(min_length=1, max_length=240)
    quantity: int = Field(ge=1, le=10_000)
    price: Decimal = Field(ge=0)


class CustomOrderInput(BaseModel):
    order_id: str = Field(min_length=1, max_length=180)
    order_number: str | None = Field(default=None, max_length=80)
    customer_name: str = Field(min_length=1, max_length=180)
    customer_phone: str = Field(min_length=8, max_length=32)
    amount: Decimal = Field(ge=0)
    currency: str = Field(default="SAR", min_length=3, max_length=3)
    payment_method: str = Field(default="COD", max_length=32)
    items: list[CustomOrderItem] = Field(default_factory=list, max_length=200)
    shipping_city: str | None = Field(default=None, max_length=120)
    shipping_address: str | None = Field(default=None, max_length=500)
    checkout_vpn_detected: bool = False

    @field_validator("customer_phone")
    @classmethod
    def normalize_customer_phone(cls, value: str) -> str:
        try:
            parsed = phonenumbers.parse(value, None)
        except phonenumbers.NumberParseException as exc:
            raise ValueError("Use an international E.164 phone number") from exc
        if not phonenumbers.is_valid_number(parsed):
            raise ValueError("Invalid customer phone number")
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()


class BusinessLeadInput(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    company: str = Field(min_length=2, max_length=180)
    whatsapp: str = Field(min_length=8, max_length=32)
    email: EmailStr
    platform: str
    monthly_orders: str
    selected_plan: str = "pilot"
    session_id: str | None = Field(default=None, min_length=8, max_length=64)
    contact_consent: bool
    consent_timestamp: datetime
    utm_source: str | None = Field(default=None, max_length=120)
    utm_medium: str | None = Field(default=None, max_length=120)
    utm_campaign: str | None = Field(default=None, max_length=160)
    utm_content: str | None = Field(default=None, max_length=160)
    utm_term: str | None = Field(default=None, max_length=160)
    referrer: str | None = Field(default=None, max_length=2000)
    landing_page: str | None = Field(default=None, max_length=2000)
    gotcha: str = Field(default="", alias="_gotcha", max_length=200)

    @field_validator("whatsapp")
    @classmethod
    def normalize_whatsapp(cls, value: str) -> str:
        try:
            parsed = phonenumbers.parse(value, None)
        except phonenumbers.NumberParseException as exc:
            raise ValueError("Use an international phone number, for example +9665...") from exc
        if not phonenumbers.is_valid_number(parsed):
            raise ValueError("Invalid WhatsApp number")
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)

    @field_validator("platform")
    @classmethod
    def supported_platform(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"salla", "zid", "shopify", "woocommerce", "custom", "other"}:
            raise ValueError("Unsupported platform")
        return normalized

    @field_validator("monthly_orders")
    @classmethod
    def valid_order_range(cls, value: str) -> str:
        normalized = value.strip()
        if normalized not in {"under_100", "100_299", "300_999", "1000_4999", "5000_plus"}:
            raise ValueError("Unsupported monthly order range")
        return normalized

    @field_validator("selected_plan")
    @classmethod
    def valid_selected_plan(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"pilot", "starter", "growth", "scale"}:
            raise ValueError("Unsupported selected plan")
        return normalized

    @model_validator(mode="after")
    def consent_is_required(self):
        if not self.contact_consent:
            raise ValueError("Contact consent is required")
        return self


class BusinessLeadCreated(BaseModel):
    id: uuid.UUID
    status: str = "received"


class AcquisitionProspectInput(BaseModel):
    company: str = Field(min_length=2, max_length=180)
    website: str = Field(min_length=8, max_length=500)
    source_url: str = Field(min_length=8, max_length=1000)
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    platform: str | None = Field(default=None, max_length=32)
    public_email: EmailStr | None = None
    public_phone: str | None = Field(default=None, max_length=40)
    social_profiles: dict[str, str] = Field(default_factory=dict)
    evidence: dict[str, str | int | float | bool] = Field(default_factory=dict)
    message_draft: str | None = Field(default=None, max_length=2500)

    @field_validator("country_code")
    @classmethod
    def acquisition_gcc_country(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.upper()
        if normalized not in {"SA", "AE", "KW", "BH", "QA", "OM"}:
            raise ValueError("Prospect must be located in a GCC country")
        return normalized

    @field_validator("platform")
    @classmethod
    def acquisition_platform(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        if normalized not in {"salla", "zid", "shopify", "woocommerce", "custom", "other"}:
            raise ValueError("Unsupported platform")
        return normalized


class AcquisitionDecisionInput(BaseModel):
    decision: str

    @field_validator("decision")
    @classmethod
    def supported_decision(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"approved", "rejected", "contacted", "replied", "converted"}:
            raise ValueError("Unsupported acquisition decision")
        return normalized


class AcquisitionProgressInput(BaseModel):
    run_id: str = Field(min_length=4, max_length=100)
    stage: str = Field(min_length=2, max_length=80)
    processed: int = Field(default=0, ge=0)
    qualified: int = Field(default=0, ge=0)
    skipped: int = Field(default=0, ge=0)
    message: str | None = Field(default=None, max_length=500)


class FunnelEventInput(BaseModel):
    event_name: str
    session_id: str = Field(min_length=8, max_length=64)
    path: str = Field(min_length=1, max_length=500)
    utm_source: str | None = Field(default=None, max_length=120)
    utm_medium: str | None = Field(default=None, max_length=120)
    utm_campaign: str | None = Field(default=None, max_length=160)
    utm_content: str | None = Field(default=None, max_length=160)
    utm_term: str | None = Field(default=None, max_length=160)
    referrer: str | None = Field(default=None, max_length=2000)
    properties: dict[str, str | int | float | bool] = Field(default_factory=dict)

    @field_validator("event_name")
    @classmethod
    def supported_event(cls, value: str) -> str:
        if value not in {
            "page_view",
            "calculator_complete",
            "pricing_select",
            "lead_form_start",
            "lead_submit",
        }:
            raise ValueError("Unsupported funnel event")
        return value


class DataDeletionInput(BaseModel):
    password: str = Field(min_length=1, max_length=128)
