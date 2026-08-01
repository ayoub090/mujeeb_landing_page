import hashlib
import hmac
import json

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_session
from app.models import WebhookEvent

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])
settings = get_settings()


def signature_ok(raw: bytes, received: str | None, secret: str, prefix: str = "") -> bool:
    if not received or not secret:
        return False
    digest = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"{prefix}{digest}", received)


async def persist_event(provider: str, raw: bytes, payload: dict, session: AsyncSession) -> bool:
    event_type = str(payload.get("event") or payload.get("eventType") or payload.get("topic") or "unknown")
    supplied_id = payload.get("id") or payload.get("event_id") or payload.get("webhook_id")
    event_key = str(supplied_id or hashlib.sha256(raw).hexdigest())
    exists = await session.scalar(
        select(WebhookEvent.id).where(
            WebhookEvent.provider == provider, WebhookEvent.event_key == event_key
        )
    )
    if exists:
        return False
    session.add(WebhookEvent(
        provider=provider, event_key=event_key, payload_hash=hashlib.sha256(raw).hexdigest(),
        event_type=event_type, payload=payload, status="received",
    ))
    await session.commit()
    return True


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
    created = await persist_event("meta", raw, payload, session)
    return {"received": True, "duplicate": not created}


@router.post("/salla")
async def receive_salla(
    request: Request,
    x_salla_signature: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
):
    raw = await request.body()
    candidate = x_salla_signature or (authorization.removeprefix("Bearer ") if authorization else None)
    if not signature_ok(raw, candidate, settings.salla_webhook_secret):
        raise HTTPException(status_code=401, detail="Invalid Salla signature")
    payload = json.loads(raw)
    created = await persist_event("salla", raw, payload, session)
    return {"received": True, "duplicate": not created}


@router.post("/zid")
async def receive_zid(
    request: Request,
    x_zid_signature: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
):
    raw = await request.body()
    candidate = x_zid_signature or (authorization.removeprefix("Bearer ") if authorization else None)
    if not signature_ok(raw, candidate, settings.zid_webhook_secret):
        raise HTTPException(status_code=401, detail="Invalid Zid signature")
    payload = json.loads(raw)
    created = await persist_event("zid", raw, payload, session)
    return {"received": True, "duplicate": not created}
