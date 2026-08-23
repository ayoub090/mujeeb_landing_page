from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.services.evolution_outreach import (
    check_instance_connection,
    fetch_and_send_qr_to_telegram,
    init_evolution_instance,
    send_evolution_media,
    send_evolution_text,
)

logger = logging.getLogger("mujeeb.evolution_router")

router = APIRouter(prefix="/api/evolution", tags=["evolution"])


class SendTextInput(BaseModel):
    phone: str
    message: str


class SendMediaInput(BaseModel):
    phone: str
    media_url: str
    caption: str
    media_type: str = "video"


@router.get("/qr")
async def trigger_qr_to_telegram() -> dict[str, Any]:
    """Initialize instance and send the fresh WhatsApp QR code directly to Telegram."""
    # 1. Ensure instance exists
    await init_evolution_instance()
    # 2. Fetch and send QR code photo to Telegram
    success = await fetch_and_send_qr_to_telegram()
    if success:
        return {"status": "success", "message": "QR Code sent directly to your Telegram bot (@AyoublidafBot)!"}
    else:
        # Check if already connected
        conn = await check_instance_connection()
        state = conn.get("instance", {}).get("state")
        if state == "open":
            return {"status": "connected", "message": "WhatsApp is already connected and active!"}
        return {"status": "error", "message": "Could not generate QR. Please ensure Evolution API is running.", "details": conn}


@router.get("/status")
async def get_evolution_status() -> dict[str, Any]:
    """Check live connection state of your private WhatsApp instance."""
    return await check_instance_connection()


@router.post("/send-text")
async def send_text(payload: SendTextInput) -> dict[str, Any]:
    return await send_evolution_text(phone=payload.phone, message=payload.message)


@router.post("/send-media")
async def send_media(payload: SendMediaInput) -> dict[str, Any]:
    return await send_evolution_media(
        phone=payload.phone,
        media_url=payload.media_url,
        caption=payload.caption,
        media_type=payload.media_type
    )
