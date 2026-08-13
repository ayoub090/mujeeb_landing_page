import enum
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class Platform(str, enum.Enum):
    salla = "salla"
    zid = "zid"
    shopify = "shopify"
    custom = "custom"


class OrderStatus(str, enum.Enum):
    pending = "pending"
    awaiting_customer = "awaiting_customer"
    confirmed = "confirmed"
    cancelled = "cancelled"
    human_follow_up = "human_follow_up"
    shipped = "shipped"
    delivered = "delivered"
    returned = "returned"


class FSMState(str, enum.Enum):
    order_received = "ORDER_RECEIVED"
    awaiting_confirmation = "AWAITING_CONFIRMATION"
    awaiting_address_choice = "AWAITING_ADDRESS_CHOICE"
    reverse_geo = "REVERSE_GEO"
    llm_parser_strict = "LLM_PARSER_STRICT"
    confirm_address_text = "CONFIRM_ADDRESS_TEXT"
    upsell_pitch = "UPSELL_PITCH"
    modify_variants = "MODIFY_VARIANTS"
    final_store_sync = "FINAL_STORE_SYNC"
    order_confirmed = "ORDER_CONFIRMED"
    order_cancelled = "ORDER_CANCELLED"
    tracking_active = "TRACKING_ACTIVE"


class RiskLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(160))
    phone_encrypted: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    stores: Mapped[list["Store"]] = relationship(back_populates="owner", cascade="all, delete-orphan")


class Store(Base):
    __tablename__ = "stores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    platform: Mapped[Platform] = mapped_column(Enum(Platform, name="platform_type"), default=Platform.custom)
    currency: Mapped[str] = mapped_column(String(3), default="SAR")
    country_code: Mapped[str] = mapped_column(String(2), default="SA")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    owner: Mapped[User] = relationship(back_populates="stores")
    integrations: Mapped[list["Integration"]] = relationship(cascade="all, delete-orphan")
    whatsapp_accounts: Mapped[list["WhatsAppAccount"]] = relationship(cascade="all, delete-orphan")
    orders: Mapped[list["Order"]] = relationship(cascade="all, delete-orphan")
    subscription: Mapped["Subscription | None"] = relationship(
        back_populates="store", cascade="all, delete-orphan", uselist=False
    )
    api_keys: Mapped[list["StoreApiKey"]] = relationship(cascade="all, delete-orphan")


# The product language calls this entity a Merchant; the existing schema keeps
# the stable `stores` table name for backwards compatibility with the dashboard.
Merchant = Store


class StoreApiKey(Base):
    __tablename__ = "store_api_keys"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(80), default="Default")
    prefix: Mapped[str] = mapped_column(String(20), index=True)
    secret_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Integration(Base):
    __tablename__ = "integrations"
    __table_args__ = (UniqueConstraint("store_id", "platform", name="uq_store_platform"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), index=True)
    platform: Mapped[Platform] = mapped_column(Enum(Platform, name="integration_platform"))
    external_store_id: Mapped[str | None] = mapped_column(String(160))
    access_token_encrypted: Mapped[str] = mapped_column(Text)
    refresh_token_encrypted: Mapped[str | None] = mapped_column(Text)
    auxiliary_token_encrypted: Mapped[str | None] = mapped_column(Text)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_connected: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class WhatsAppAccount(Base):
    __tablename__ = "whatsapp_accounts"
    __table_args__ = (UniqueConstraint("store_id", "phone_number_id", name="uq_store_phone_number_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), index=True)
    waba_id: Mapped[str] = mapped_column(String(128))
    phone_number_id: Mapped[str] = mapped_column(String(128))
    display_phone_encrypted: Mapped[str | None] = mapped_column(Text)
    access_token_encrypted: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="connected")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class WaapiConnection(Base):
    __tablename__ = "waapi_connections"
    __table_args__ = (UniqueConstraint("store_id", name="uq_waapi_store"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), index=True)
    instance_id: Mapped[str] = mapped_column(String(64))
    api_token_encrypted: Mapped[str] = mapped_column(Text)
    webhook_token_encrypted: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="configured")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = (UniqueConstraint("store_id", "phone_hash", name="uq_store_phone_hash"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), index=True)
    name_encrypted: Mapped[str | None] = mapped_column(Text)
    phone_encrypted: Mapped[str] = mapped_column(Text)
    phone_hash: Mapped[str] = mapped_column(String(64), index=True)
    rto_count: Mapped[int] = mapped_column(Integer, default=0)
    total_orders: Mapped[int] = mapped_column(Integer, default=0)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    marketing_opt_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("store_id", "external_order_id", name="uq_store_external_order"),
        Index("ix_orders_store_status_created", "store_id", "status", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), index=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.id", ondelete="RESTRICT"), index=True)
    external_order_id: Mapped[str] = mapped_column(String(180))
    external_order_number: Mapped[str | None] = mapped_column(String(80))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=0)
    currency: Mapped[str] = mapped_column(String(3), default="SAR")
    payment_method: Mapped[str] = mapped_column(String(32), default="cod")
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus, name="order_status"), default=OrderStatus.pending)
    risk_score: Mapped[int] = mapped_column(Integer, default=0)
    risk_level: Mapped[RiskLevel] = mapped_column(Enum(RiskLevel, name="risk_level"), default=RiskLevel.low)
    risk_reasons: Mapped[dict] = mapped_column(JSON, default=dict)
    items: Mapped[list] = mapped_column(JSON, default=list)
    shipping_city: Mapped[str | None] = mapped_column(String(120))
    shipping_address_encrypted: Mapped[str | None] = mapped_column(Text)
    gps_lat: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    gps_lng: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    address_data: Mapped[dict] = mapped_column(JSON, default=dict)
    llm_decision: Mapped[dict] = mapped_column(JSON, default=dict)
    upsell_status: Mapped[str] = mapped_column(String(32), default="not_offered")
    tracking_number: Mapped[str | None] = mapped_column(String(120))
    carrier_name: Mapped[str | None] = mapped_column(String(80))
    billing_status: Mapped[str] = mapped_column(String(32), default="UNBILLED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class FSMConversation(Base):
    __tablename__ = "fsm_conversations"
    __table_args__ = (UniqueConstraint("phone_number", "order_id", name="uq_fsm_phone_order"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_number: Mapped[str] = mapped_column(String(32), index=True)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    current_state: Mapped[FSMState] = mapped_column(
        Enum(FSMState, name="fsm_state"), default=FSMState.order_received, index=True
    )
    session_data: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("orders.id", ondelete="SET NULL"), index=True)
    store_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(32))
    direction: Mapped[str] = mapped_column(String(16))
    message_sid: Mapped[str | None] = mapped_column(String(180), unique=True)
    status: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), unique=True)
    plan: Mapped[str] = mapped_column(String(32), default="free")
    status: Mapped[str] = mapped_column(String(32), default="active")
    orders_count_this_month: Mapped[int] = mapped_column(Integer, default=0)
    # The free pilot is consumed only after a customer successfully confirms
    # an order. Paid plans continue to use their normal monthly allowance.
    free_confirmations_remaining: Mapped[int] = mapped_column(Integer, default=50)
    creem_customer_id: Mapped[str | None] = mapped_column(String(128))
    creem_subscription_id: Mapped[str | None] = mapped_column(String(128), unique=True)
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    store: Mapped[Store] = relationship(back_populates="subscription")


class OAuthState(Base):
    __tablename__ = "oauth_states"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(32))
    state_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class WebhookEvent(Base):
    __tablename__ = "webhook_events"
    __table_args__ = (UniqueConstraint("provider", "event_key", name="uq_provider_event"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column(String(32), index=True)
    event_key: Mapped[str] = mapped_column(String(128))
    payload_hash: Mapped[str] = mapped_column(String(64))
    event_type: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(32), default="received")
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ConsentLog(Base):
    __tablename__ = "consent_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), index=True)
    customer_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("customers.id", ondelete="SET NULL"))
    purpose: Mapped[str] = mapped_column(String(80))
    source: Mapped[str] = mapped_column(String(80))
    text_version: Mapped[str] = mapped_column(String(32))
    ip_hash: Mapped[str | None] = mapped_column(String(64))
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class BusinessLead(Base):
    __tablename__ = "business_leads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name_encrypted: Mapped[str] = mapped_column(Text)
    company: Mapped[str] = mapped_column(String(180))
    whatsapp_encrypted: Mapped[str] = mapped_column(Text)
    whatsapp_hash: Mapped[str] = mapped_column(String(64), index=True)
    email_encrypted: Mapped[str] = mapped_column(Text)
    email_hash: Mapped[str] = mapped_column(String(64), index=True)
    platform: Mapped[str] = mapped_column(String(32))
    monthly_orders: Mapped[str] = mapped_column(String(32))
    selected_plan: Mapped[str] = mapped_column(String(32), default="pilot", index=True)
    session_id: Mapped[str | None] = mapped_column(String(64), index=True)
    attribution: Mapped[dict] = mapped_column(JSON, default=dict)
    referrer: Mapped[str | None] = mapped_column(Text)
    landing_page: Mapped[str | None] = mapped_column(Text)
    consent_text_version: Mapped[str] = mapped_column(String(32), default="lead-v1")
    consent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ip_hash: Mapped[str | None] = mapped_column(String(64))
    user_agent_hash: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="new", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class FunnelEvent(Base):
    __tablename__ = "funnel_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_name: Mapped[str] = mapped_column(String(48), index=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    path: Mapped[str] = mapped_column(String(500))
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    store_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("stores.id", ondelete="SET NULL"), index=True
    )
    source: Mapped[str] = mapped_column(String(32), default="client", index=True)
    properties: Mapped[dict] = mapped_column(JSON, default=dict)
    attribution: Mapped[dict] = mapped_column(JSON, default=dict)
    referrer: Mapped[str | None] = mapped_column(Text)
    ip_hash: Mapped[str | None] = mapped_column(String(64))
    user_agent_hash: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class EmailJob(Base):
    __tablename__ = "email_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dedupe_key: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    kind: Mapped[str] = mapped_column(String(64), index=True)
    recipient_encrypted: Mapped[str] = mapped_column(Text)
    recipient_hash: Mapped[str] = mapped_column(String(64), index=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="queued", index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    next_attempt_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    last_error: Mapped[str | None] = mapped_column(Text)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DataDeletionRequest(Base):
    __tablename__ = "data_deletion_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    email_hash: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), default="scheduled", index=True)
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
