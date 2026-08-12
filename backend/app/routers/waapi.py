from __future__ import annotations

import secrets
import uuid

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.config import get_settings
from app.crypto import encrypt_text, stable_hash
from app.database import get_session
from app.models import Store, User, WaapiConnection

router = APIRouter(prefix="/api/waapi", tags=["waapi"])

class ConnectInput(BaseModel):
    store_id: uuid.UUID
    instance_id: str = Field(min_length=1, max_length=64)
    api_token: str = Field(min_length=10)

async def owned(store_id, user, session):
    store = await session.scalar(select(Store).where(Store.id == store_id, Store.owner_id == user.id))
    if not store: raise HTTPException(404, "Store not found")
    return store

@router.post("/connect")
async def connect(payload: ConnectInput, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    await owned(payload.store_id, user, session)
    if "@" in payload.instance_id or not payload.instance_id.strip().isdigit():
        raise HTTPException(422, "WAAPI instance ID must be the numeric ID from your WaAPI dashboard")
    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(f"{str(settings.waapi_base_url).rstrip('/')}/instances/{payload.instance_id}", headers={"Authorization": f"Bearer {payload.api_token}", "Accept":"application/json"})
    except httpx.HTTPError as exc:
        raise HTTPException(502, "WAAPI is temporarily unreachable. Please retry.") from exc
    if response.is_error: raise HTTPException(502, "WAAPI instance could not be verified")
    webhook_token = secrets.token_urlsafe(32)
    row = await session.scalar(select(WaapiConnection).where(WaapiConnection.store_id == payload.store_id))
    if not row:
        row = WaapiConnection(store_id=payload.store_id, instance_id=payload.instance_id, api_token_encrypted=encrypt_text(payload.api_token), webhook_token_encrypted=encrypt_text(webhook_token))
        session.add(row)
    else:
        row.instance_id = payload.instance_id; row.api_token_encrypted = encrypt_text(payload.api_token); row.webhook_token_encrypted = encrypt_text(webhook_token); row.status = "configured"
    await session.commit()
    return {"status":"connected", "instance_id":payload.instance_id, "webhook_path":f"/api/waapi/webhooks/{webhook_token}"}

@router.get("/status")
async def status(store_id: uuid.UUID, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    await owned(store_id, user, session)
    row = await session.scalar(select(WaapiConnection).where(WaapiConnection.store_id == store_id))
    if not row: return {"configured":False,"connected":False}
    settings = get_settings()
    from app.crypto import decrypt_text
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(f"{str(settings.waapi_base_url).rstrip('/')}/instances/{row.instance_id}/client/status", headers={"Authorization":f"Bearer {decrypt_text(row.api_token_encrypted)}","Accept":"application/json"})
    except httpx.HTTPError:
        return {"configured":True,"connected":False,"instance_id":row.instance_id,"provider":"waapi","error":"provider_unreachable"}
    return {"configured":True,"connected":response.is_success,"instance_id":row.instance_id,"provider":"waapi"}

@router.post("/webhooks/{token}", status_code=202)
async def webhook(token: str, request: Request, session: AsyncSession = Depends(get_session)):
    raw = await request.json()
    rows = await session.scalars(select(WaapiConnection))
    match = None
    from app.crypto import decrypt_text
    for row in rows:
        if row.webhook_token_encrypted and secrets.compare_digest(decrypt_text(row.webhook_token_encrypted), token): match = row; break
    if not match: raise HTTPException(401, "Invalid webhook token")
    return {"received":True,"store_id":str(match.store_id),"event":raw.get("event"),"instance_id":raw.get("instanceId")}
