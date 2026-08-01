import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.config import get_settings
from app.crypto import encrypt_text
from app.database import get_session
from app.models import Integration, OAuthState, Platform, Store, User
from app.schemas import OAuthStartInput, UrlOut

router = APIRouter(prefix="/api/integrations", tags=["integrations"])
settings = get_settings()


async def ensure_owned_store(store_id: uuid.UUID, user_id: uuid.UUID, session: AsyncSession) -> Store:
    store = await session.scalar(select(Store).where(Store.id == store_id, Store.owner_id == user_id))
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    return store


async def make_state(provider: str, store_id: uuid.UUID, session: AsyncSession) -> str:
    state = secrets.token_urlsafe(32)
    session.add(
        OAuthState(
            provider=provider,
            store_id=store_id,
            state_hash=hashlib.sha256(state.encode()).hexdigest(),
            expires_at=datetime.now(UTC) + timedelta(minutes=10),
        )
    )
    await session.commit()
    return state


async def consume_state(provider: str, state: str, session: AsyncSession) -> OAuthState:
    now = datetime.now(UTC)
    row = await session.scalar(
        select(OAuthState).where(
            OAuthState.provider == provider,
            OAuthState.state_hash == hashlib.sha256(state.encode()).hexdigest(),
            OAuthState.consumed_at.is_(None),
            OAuthState.expires_at > now,
        )
    )
    if not row:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
    row.consumed_at = now
    await session.flush()
    return row


@router.post("/salla/start", response_model=UrlOut)
async def start_salla(
    payload: OAuthStartInput,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await ensure_owned_store(payload.store_id, user.id, session)
    if not settings.salla_client_id:
        raise HTTPException(status_code=503, detail="Salla integration is not configured")
    state = await make_state("salla", payload.store_id, session)
    params = {
        "client_id": settings.salla_client_id,
        "redirect_uri": settings.salla_redirect_uri,
        "response_type": "code",
        "scope": "offline_access read_orders write_orders read_customers",
        "state": state,
    }
    return UrlOut(url=f"https://accounts.salla.sa/oauth2/auth?{urlencode(params)}")


@router.get("/salla/callback")
async def salla_callback(
    code: str = Query(...),
    state: str = Query(...),
    session: AsyncSession = Depends(get_session),
):
    state_row = await consume_state("salla", state, session)
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            "https://accounts.salla.sa/oauth2/token",
            data={
                "client_id": settings.salla_client_id,
                "client_secret": settings.salla_client_secret,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.salla_redirect_uri,
            },
        )
        response.raise_for_status()
    token = response.json()
    await upsert_integration(state_row.store_id, Platform.salla, token, session)
    await session.commit()
    return RedirectResponse(f"{settings.frontend_origin}/dashboard/integrations?connected=salla")


@router.post("/zid/start", response_model=UrlOut)
async def start_zid(
    payload: OAuthStartInput,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await ensure_owned_store(payload.store_id, user.id, session)
    if not settings.zid_client_id:
        raise HTTPException(status_code=503, detail="Zid integration is not configured")
    state = await make_state("zid", payload.store_id, session)
    params = {
        "client_id": settings.zid_client_id,
        "redirect_uri": settings.zid_redirect_uri,
        "response_type": "code",
        "state": state,
    }
    return UrlOut(url=f"https://oauth.zid.sa/oauth/authorize?{urlencode(params)}")


@router.get("/zid/callback")
async def zid_callback(
    code: str = Query(...),
    state: str = Query(...),
    session: AsyncSession = Depends(get_session),
):
    state_row = await consume_state("zid", state, session)
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            "https://oauth.zid.sa/oauth/token",
            data={
                "client_id": settings.zid_client_id,
                "client_secret": settings.zid_client_secret,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.zid_redirect_uri,
            },
        )
        response.raise_for_status()
    token = response.json()
    await upsert_integration(state_row.store_id, Platform.zid, token, session)
    await session.commit()
    return RedirectResponse(f"{settings.frontend_origin}/dashboard/integrations?connected=zid")


async def upsert_integration(
    store_id: uuid.UUID, platform: Platform, token: dict, session: AsyncSession
) -> None:
    existing = await session.scalar(
        select(Integration).where(Integration.store_id == store_id, Integration.platform == platform)
    )
    expires_at = None
    if token.get("expires_in"):
        expires_at = datetime.now(UTC) + timedelta(seconds=int(token["expires_in"]))
    values = {
        "access_token_encrypted": encrypt_text(token["access_token"]),
        "refresh_token_encrypted": encrypt_text(token["refresh_token"]) if token.get("refresh_token") else None,
        "auxiliary_token_encrypted": encrypt_text(token["authorization"]) if token.get("authorization") else None,
        "expires_at": expires_at,
        "is_connected": True,
    }
    if existing:
        for key, value in values.items():
            setattr(existing, key, value)
    else:
        session.add(Integration(store_id=store_id, platform=platform, **values))

