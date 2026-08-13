from __future__ import annotations

import secrets
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_superadmin
from app.database import get_session
from app.models import Store, User

router = APIRouter(prefix="/api/dev/whatsapp", tags=["development"])
_sessions: dict[str, dict] = {}


class SessionIn(BaseModel):
    store_id: uuid.UUID


class EventIn(BaseModel):
    event: str
    payload: dict = {}


@router.post("/session")
async def create_session(payload: SessionIn, user: User = Depends(require_superadmin), session: AsyncSession = Depends(get_session)):
    # Query explicitly instead of touching the async lazy ``user.stores`` relationship.
    # The latter raises MissingGreenlet in production and made the pilot button fail.
    store = await session.scalar(select(Store).where(Store.id == payload.store_id, Store.owner_id == user.id))
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    session_id = secrets.token_urlsafe(18)
    _sessions[session_id] = {
        "id": session_id,
        "store_id": str(payload.store_id),
        "status": "qr_ready",
        "mode": "local_simulator",
        "created_at": int(time.time()),
        "qr_payload": f"mujeeb-dev://whatsapp/{session_id}",
        "events": [],
    }
    return _sessions[session_id]


@router.get("/session/{session_id}")
async def get_session(session_id: str, user: User = Depends(require_superadmin), db: AsyncSession = Depends(get_session)):
    session = _sessions.get(session_id)
    store = await db.scalar(select(Store).where(Store.id == (session or {}).get("store_id"), Store.owner_id == user.id))
    if not session or not store:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/session/{session_id}/event")
async def add_event(session_id: str, payload: EventIn, user: User = Depends(require_superadmin), db: AsyncSession = Depends(get_session)):
    session = _sessions.get(session_id)
    store = await db.scalar(select(Store).where(Store.id == (session or {}).get("store_id"), Store.owner_id == user.id))
    if not session or not store:
        raise HTTPException(status_code=404, detail="Session not found")
    session["status"] = "connected" if payload.event == "qr_scanned" else "running"
    session["events"].append({"event": payload.event, "payload": payload.payload, "at": int(time.time())})
    return session
