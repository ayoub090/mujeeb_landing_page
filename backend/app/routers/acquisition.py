import hmac
import uuid
from datetime import UTC, datetime

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_session
from app.models import AcquisitionProspect
from app.schemas import AcquisitionDecisionInput, AcquisitionProgressInput, AcquisitionProspectInput
from app.services.prospecting import canonicalize_website, prospect_score
from app.services.telegram import prospect_message, send_telegram_notification

router = APIRouter(prefix="/api/acquisition", tags=["acquisition"])


def require_acquisition_key(x_mujeeb_acquisition_key: str | None = Header(default=None)) -> None:
    expected = get_settings().acquisition_admin_key
    if not expected or not x_mujeeb_acquisition_key or not hmac.compare_digest(
        expected, x_mujeeb_acquisition_key
    ):
        raise HTTPException(status_code=401, detail="Acquisition access denied")


@router.post("/extract", dependencies=[Depends(require_acquisition_key)])
async def extract_public_business(
    payload: dict,
    x_mujeeb_acquisition_key: str | None = Header(default=None),
):
    """Authenticated proxy to the private, locally hosted ScrapeGraphAI service."""

    if not isinstance(payload.get("url"), str):
        raise HTTPException(status_code=422, detail="url is required")
    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{str(settings.acquisition_scraper_url).rstrip('/')}/extract",
                headers={"X-Mujeeb-Acquisition-Key": x_mujeeb_acquisition_key or ""},
                json={"url": payload["url"], "country_hint": payload.get("country_hint")},
            )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=503, detail="Local extractor is unavailable") from exc
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail="Local extractor rejected the request")
    return response.json()


@router.post("/prospects", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_acquisition_key)])
async def ingest_prospect(
    payload: AcquisitionProspectInput,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    try:
        canonical = canonicalize_website(payload.website)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    existing = await session.scalar(
        select(AcquisitionProspect).where(AcquisitionProspect.canonical_website == canonical)
    )
    if existing:
        return {"id": str(existing.id), "status": "duplicate", "score": existing.score}

    score = prospect_score(
        country_code=payload.country_code,
        platform=payload.platform,
        public_email=str(payload.public_email) if payload.public_email else None,
        public_phone=payload.public_phone,
        evidence=payload.evidence,
    )
    prospect = AcquisitionProspect(
        company=payload.company.strip(),
        canonical_website=canonical,
        source_url=payload.source_url,
        country_code=payload.country_code,
        platform=payload.platform,
        public_email=str(payload.public_email) if payload.public_email else None,
        public_phone=payload.public_phone,
        social_profiles=payload.social_profiles,
        evidence=payload.evidence,
        score=score,
        status="qualified" if score >= 60 else "research",
        message_draft=payload.message_draft,
    )
    session.add(prospect)
    await session.commit()
    await session.refresh(prospect)
    if score >= 60:
        background_tasks.add_task(
            send_telegram_notification,
            prospect_message(
                company=prospect.company,
                website=prospect.canonical_website,
                score=prospect.score,
                platform=prospect.platform,
                country=prospect.country_code,
            ),
        )
    return {"id": str(prospect.id), "status": prospect.status, "score": prospect.score}


@router.post("/progress", status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(require_acquisition_key)])
async def acquisition_progress(payload: AcquisitionProgressInput, background_tasks: BackgroundTasks):
    text = (
        f"<b>Mujeeb acquisition · {payload.stage}</b>\n"
        f"Run : {payload.run_id}\n"
        f"Traités : {payload.processed}\nQualifiés : {payload.qualified}\nIgnorés : {payload.skipped}"
    )
    if payload.message:
        text += f"\n{payload.message}"
    background_tasks.add_task(send_telegram_notification, text)
    return {"status": "accepted"}


@router.patch("/prospects/{prospect_id}", dependencies=[Depends(require_acquisition_key)])
async def decide_prospect(
    prospect_id: uuid.UUID,
    payload: AcquisitionDecisionInput,
    session: AsyncSession = Depends(get_session),
):
    prospect = await session.get(AcquisitionProspect, prospect_id)
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")
    prospect.status = payload.decision
    if payload.decision == "contacted":
        prospect.last_contacted_at = datetime.now(UTC)
        prospect.contact_attempts += 1
    await session.commit()
    return {"id": str(prospect.id), "status": prospect.status}


@router.get("/prospects", dependencies=[Depends(require_acquisition_key)])
async def list_prospects(
    prospect_status: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
):
    query = select(AcquisitionProspect).order_by(
        AcquisitionProspect.score.desc(), AcquisitionProspect.discovered_at.desc()
    )
    if prospect_status:
        query = query.where(AcquisitionProspect.status == prospect_status)
    rows = list((await session.scalars(query.limit(limit))).all())
    return {
        "items": [
            {
                "id": str(item.id),
                "company": item.company,
                "website": item.canonical_website,
                "country_code": item.country_code,
                "platform": item.platform,
                "public_email": item.public_email,
                "public_phone": item.public_phone,
                "score": item.score,
                "status": item.status,
                "message_draft": item.message_draft,
                "contact_attempts": item.contact_attempts,
                "discovered_at": item.discovered_at,
            }
            for item in rows
        ],
        "count": len(rows),
        "auto_send_enabled": get_settings().acquisition_auto_send_enabled,
    }


@router.get("/summary", dependencies=[Depends(require_acquisition_key)])
async def acquisition_summary(session: AsyncSession = Depends(get_session)):
    rows = (await session.execute(
        select(AcquisitionProspect.status, func.count(AcquisitionProspect.id)).group_by(
            AcquisitionProspect.status
        )
    )).all()
    return {
        "by_status": {name: count for name, count in rows},
        "daily_limit": get_settings().acquisition_daily_limit,
        "auto_send_enabled": get_settings().acquisition_auto_send_enabled,
    }
