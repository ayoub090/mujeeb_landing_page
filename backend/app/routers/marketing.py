import hmac
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Header,
    HTTPException,
    Query,
    Request,
    status,
)
from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.crypto import decrypt_text, encrypt_text, stable_hash
from app.database import get_session
from app.models import BusinessLead, FunnelEvent
from app.schemas import BusinessLeadCreated, BusinessLeadInput, FunnelEventInput
from app.services.capi import send_capi_event

router = APIRouter(prefix="/api/marketing", tags=["marketing"])


def _source_ip(request: Request) -> str:
    if get_settings().trust_proxy_headers:
        forwarded = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        if forwarded:
            return forwarded
    return request.client.host if request.client else "unknown"


def _request_hashes(request: Request) -> tuple[str, str]:
    return (
        stable_hash(f"lead-ip:{_source_ip(request)}"),
        stable_hash(f"lead-agent:{request.headers.get('user-agent', 'unknown')}"),
    )


def _attribution(payload: BusinessLeadInput | FunnelEventInput) -> dict[str, str]:
    return {
        key: value
        for key in ("utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term")
        if (value := getattr(payload, key))
    }


@router.post("/leads", response_model=BusinessLeadCreated, status_code=status.HTTP_201_CREATED)
async def create_lead(
    payload: BusinessLeadInput,
    request: Request,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    # Silently accept honeypot submissions so bots cannot tune around the filter.
    if payload.gotcha:
        return BusinessLeadCreated(id=uuid.uuid4())

    ip_hash, user_agent_hash = _request_hashes(request)
    lead = BusinessLead(
        full_name_encrypted=encrypt_text(payload.name.strip()),
        company=payload.company.strip(),
        whatsapp_encrypted=encrypt_text(payload.whatsapp),
        whatsapp_hash=stable_hash(payload.whatsapp),
        email_encrypted=encrypt_text(str(payload.email).lower()),
        email_hash=stable_hash(str(payload.email)),
        platform=payload.platform,
        monthly_orders=payload.monthly_orders,
        selected_plan=payload.selected_plan,
        session_id=payload.session_id,
        attribution=_attribution(payload),
        referrer=payload.referrer,
        landing_page=payload.landing_page,
        consent_at=payload.consent_timestamp,
        ip_hash=ip_hash,
        user_agent_hash=user_agent_hash,
    )
    session.add(lead)
    session.add(
        FunnelEvent(
            event_name="lead_created",
            session_id=payload.session_id or f"lead-{lead.id.hex}",
            path=payload.landing_page or "/",
            source="server",
            properties={"plan": payload.selected_plan, "platform": payload.platform},
            attribution=_attribution(payload),
            referrer=payload.referrer,
            ip_hash=ip_hash,
            user_agent_hash=user_agent_hash,
        )
    )
    await session.commit()
    background_tasks.add_task(
        send_capi_event,
        "Lead",
        f"lead-{lead.id}",
        email=str(payload.email),
        phone=payload.whatsapp,
        client_ip=_source_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    return BusinessLeadCreated(id=lead.id)


@router.post("/events", status_code=status.HTTP_202_ACCEPTED)
async def create_funnel_event(
    payload: FunnelEventInput,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    ip_hash, user_agent_hash = _request_hashes(request)
    session.add(
        FunnelEvent(
            event_name=payload.event_name,
            session_id=payload.session_id,
            path=payload.path,
            attribution=_attribution(payload),
            referrer=payload.referrer,
            properties=payload.properties,
            ip_hash=ip_hash,
            user_agent_hash=user_agent_hash,
        )
    )
    await session.commit()
    return {"status": "accepted"}


@router.get("/metrics")
async def conversion_metrics(
    days: int = Query(default=30, ge=1, le=365),
    x_mujeeb_analytics_key: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
):
    settings = get_settings()
    if not settings.analytics_admin_key or not x_mujeeb_analytics_key or not hmac.compare_digest(
        settings.analytics_admin_key, x_mujeeb_analytics_key
    ):
        raise HTTPException(status_code=401, detail="Analytics access denied")
    since = datetime.now(UTC) - timedelta(days=days)
    rows = (await session.execute(
        select(FunnelEvent.event_name, func.count(FunnelEvent.id), func.count(distinct(FunnelEvent.session_id)))
        .where(FunnelEvent.created_at >= since)
        .group_by(FunnelEvent.event_name)
    )).all()
    by_event = {name: {"events": count, "sessions": sessions} for name, count, sessions in rows}
    page_sessions = by_event.get("page_view", {}).get("sessions", 0)
    leads = by_event.get("lead_created", {}).get("events", 0)
    signups = by_event.get("signup_completed", {}).get("events", 0)
    connected = by_event.get("store_connected", {}).get("events", 0)
    paid = by_event.get("subscription_activated", {}).get("events", 0)

    def rate(value: int, base: int) -> float:
        return round(value / base * 100, 2) if base else 0

    return {
        "window_days": days,
        "events": by_event,
        "funnel": {
            "visitor_sessions": page_sessions,
            "leads": leads,
            "signups": signups,
            "connected_stores": connected,
            "paid_subscriptions": paid,
        },
        "conversion_rates": {
            "visitor_to_lead": rate(leads, page_sessions),
            "lead_to_signup": rate(signups, leads),
            "signup_to_connected": rate(connected, signups),
            "connected_to_paid": rate(paid, connected),
            "visitor_to_paid": rate(paid, page_sessions),
        },
        "generated_at": datetime.now(UTC),
    }


@router.get("/leads")
async def list_leads(
    limit: int = Query(default=100, ge=1, le=500),
    x_mujeeb_analytics_key: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
):
    """Private lead inbox for the owner, protected by the analytics key."""
    settings = get_settings()
    if not settings.analytics_admin_key or not x_mujeeb_analytics_key or not hmac.compare_digest(
        settings.analytics_admin_key, x_mujeeb_analytics_key
    ):
        raise HTTPException(status_code=401, detail="Analytics access denied")
    leads = list((await session.scalars(
        select(BusinessLead).order_by(BusinessLead.created_at.desc()).limit(limit)
    )).all())
    return {
        "items": [
            {
                "id": str(lead.id),
                "name": decrypt_text(lead.full_name_encrypted),
                "company": lead.company,
                "whatsapp": decrypt_text(lead.whatsapp_encrypted),
                "email": decrypt_text(lead.email_encrypted),
                "platform": lead.platform,
                "monthly_orders": lead.monthly_orders,
                "selected_plan": lead.selected_plan,
                "status": lead.status,
                "attribution": lead.attribution,
                "created_at": lead.created_at,
            }
            for lead in leads
        ],
        "count": len(leads),
    }
