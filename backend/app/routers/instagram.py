"""FastAPI router for Instagram DM Outreach and lead synchronization."""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from app.services.instagram_outreach import (
    is_authenticated,
    login_instagram,
    send_instagram_dm,
    poll_instagram_replies,
    _logged_in_user,
    _dms_sent_today,
)

router = APIRouter(prefix="/api/v1/instagram", tags=["instagram"])


class LoginRequest(BaseModel):
    username: str = Field(..., description="Instagram username or handle")
    password: str = Field(..., description="Instagram password")
    verification_code: str | None = Field(default=None, description="2FA code or SMS code")


class SendDmRequest(BaseModel):
    target_username: str = Field(..., description="Target merchant handle, e.g. store_sa")
    message: str = Field(..., description="Personalized Arabic/English pitch message")
    store_name: str | None = Field(default=None, description="Name of the store for Telegram logs")
    media_path: str | None = Field(default=None, description="Optional local path to 20s demo video or image")


@router.get("/status")
async def get_instagram_status() -> dict[str, Any]:
    return {
        "authenticated": is_authenticated(),
        "connected_account": _logged_in_user,
        "dms_sent_today": _dms_sent_today,
        "daily_limit": 30,
        "engine": "instagrapi_private_mobile"
    }


@router.post("/login")
async def login(req: LoginRequest) -> dict[str, Any]:
    result = login_instagram(req.username, req.password, req.verification_code)
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/send-dm")
async def send_dm(req: SendDmRequest, background_tasks: BackgroundTasks) -> dict[str, Any]:
    if not is_authenticated():
        raise HTTPException(status_code=401, detail="Instagram account is not authenticated. Please login first.")

    # Queue in background with humanized delay
    background_tasks.add_task(
        send_instagram_dm,
        target_username=req.target_username,
        message=req.message,
        store_name=req.store_name,
        media_path=req.media_path
    )

    return {
        "status": "queued",
        "target": req.target_username,
        "message": "DM has been queued with humanized anti-ban delay (35-65s)."
    }


@router.post("/poll-replies")
async def poll_replies() -> dict[str, Any]:
    replies = await poll_instagram_replies()
    return {"status": "ok", "new_replies_count": len(replies), "replies": replies}
