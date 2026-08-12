from __future__ import annotations

import secrets
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import get_current_user
from app.models import User

router = APIRouter(prefix="/api/dev/whatsapp", tags=["development"])
_sessions: dict[str, dict] = {}


class SessionIn(BaseModel):
    store_id: uuid.UUID


class EventIn(BaseModel):
    event: str
    payload: dict = {}


@router.post("/session")
async def create_session(payload: SessionIn, user: User = Depends(get_current_user)):
    if not any(str(store.id) == str(payload.store_id) for store in user.stores):
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
async def get_session(session_id: str, user: User = Depends(get_current_user)):
    session = _sessions.get(session_id)
    if not session or not any(session["store_id"] == str(store.id) for store in user.stores):
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/session/{session_id}/event")
async def add_event(session_id: str, payload: EventIn, user: User = Depends(get_current_user)):
    session = _sessions.get(session_id)
    if not session or not any(session["store_id"] == str(store.id) for store in user.stores):
        raise HTTPException(status_code=404, detail="Session not found")
    session["status"] = "connected" if payload.event == "qr_scanned" else "running"
    session["events"].append({"event": payload.event, "payload": payload.payload, "at": int(time.time())})
    return session
