import uuid

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.crypto import encrypt_text, stable_hash
from app.database import get_session
from app.models import BusinessLead, FunnelEvent
from app.schemas import BusinessLeadCreated, BusinessLeadInput, FunnelEventInput

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
        attribution=_attribution(payload),
        referrer=payload.referrer,
        landing_page=payload.landing_page,
        consent_at=payload.consent_timestamp,
        ip_hash=ip_hash,
        user_agent_hash=user_agent_hash,
    )
    session.add(lead)
    await session.commit()
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
            ip_hash=ip_hash,
            user_agent_hash=user_agent_hash,
        )
    )
    await session.commit()
    return {"status": "accepted"}
