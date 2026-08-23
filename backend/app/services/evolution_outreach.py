"""Dedicated Private Outreach Engine powered by Evolution API (Self-Hosted Baileys).
Exclusively for automated acquisition, Google Maps scraping outreach, and Telegram notifications.
"""
from __future__ import annotations

import asyncio
import base64
import logging
import random
from typing import Any

import httpx

from app.config import get_settings
from app.services.telegram import send_telegram_notification

logger = logging.getLogger("mujeeb.evolution_outreach")

INSTANCE_NAME = "ayoub_outreach"


async def get_headers() -> dict[str, str]:
    settings = get_settings()
    return {
        "apikey": settings.evolution_api_key,
        "Content-Type": "application/json"
    }


async def init_evolution_instance() -> dict[str, Any]:
    """Create or verify your private outreach WhatsApp instance in Evolution API."""
    settings = get_settings()
    base_url = str(settings.evolution_api_url).rstrip("/")
    headers = await get_headers()

    url = f"{base_url}/instance/create"
    payload = {
        "instanceName": INSTANCE_NAME,
        "token": settings.evolution_api_key,
        "qrcode": True,
        "integration": "WHATSAPP_BAILEYS",
        "rejectCall": True,
        "msgCall": "هذا الرقم مخصص للتواصل الآلي فقط.",
        "groupsIgnore": True,
        "alwaysOnline": True,
        "readMessages": True,
        "syncFullHistory": False
    }

    async with httpx.AsyncClient(timeout=25) as client:
        try:
            res = await client.post(url, headers=headers, json=payload)
            if res.status_code in [200, 201]:
                data = res.json()
                logger.info("Evolution instance created: %s", data)
                return data
            elif res.status_code == 403 or "already exists" in res.text:
                logger.info("Evolution instance '%s' already exists.", INSTANCE_NAME)
                return {"instance": {"instanceName": INSTANCE_NAME, "status": "exists"}}
            else:
                logger.error("Evolution init failed: %s %s", res.status_code, res.text)
                return {"error": res.text}
        except Exception as e:
            logger.error("Error connecting to Evolution API: %s", e)
            return {"error": str(e)}


async def fetch_and_send_qr_to_telegram() -> bool:
    """Fetch the latest QR code from Evolution API and send it as a photo to Telegram."""
    settings = get_settings()
    base_url = str(settings.evolution_api_url).rstrip("/")
    headers = await get_headers()

    url = f"{base_url}/instance/connect/{INSTANCE_NAME}"

    async with httpx.AsyncClient(timeout=25) as client:
        try:
            res = await client.get(url, headers=headers)
            if res.status_code == 200:
                data = res.json()
                qr_base64 = data.get("base64") or data.get("code")
                if qr_base64 and qr_base64.startswith("data:image"):
                    qr_base64 = qr_base64.split(",", 1)[1]

                if qr_base64:
                    img_bytes = base64.b64decode(qr_base64)
                    tg_token = settings.telegram_bot_token
                    tg_chat_id = settings.telegram_chat_id
                    caption = (
                        "📲 <b>SCANNEZ CE QR CODE (EVOLUTION API PRIVÉE)</b>\n\n"
                        "1. Ouvrez <b>WhatsApp</b> sur votre téléphone\n"
                        "2. Allez dans <b>Appareils connectés</b> > <b>Connecter un appareil</b>\n"
                        "3. Scannez ce QR Code ci-dessus.\n\n"
                        "⚡️ <i>Votre instance privée Evolution API sera connectée sans passer par aucun tiers payant !</i>"
                    )
                    files = {"photo": ("evolution_qr.png", img_bytes, "image/png")}
                    await client.post(
                        f"https://api.telegram.org/bot{tg_token}/sendPhoto",
                        data={"chat_id": tg_chat_id, "caption": caption, "parse_mode": "HTML"},
                        files=files,
                        timeout=20
                    )
                    return True
            return False
        except Exception as e:
            logger.error("Error fetching QR: %s", e)
            return False


async def check_instance_connection() -> dict[str, Any]:
    """Check if the private instance is currently connected and active."""
    settings = get_settings()
    base_url = str(settings.evolution_api_url).rstrip("/")
    headers = await get_headers()

    url = f"{base_url}/instance/connectionState/{INSTANCE_NAME}"

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            res = await client.get(url, headers=headers)
            if res.status_code == 200:
                return res.json()
            return {"state": "disconnected"}
        except Exception as e:
            return {"state": "error", "error": str(e)}


async def send_evolution_text(*, phone: str, message: str) -> dict[str, Any]:
    """Send text message via your private Evolution instance."""
    settings = get_settings()
    base_url = str(settings.evolution_api_url).rstrip("/")
    headers = await get_headers()

    clean_phone = "".join(filter(str.isdigit, phone))
    url = f"{base_url}/message/sendText/{INSTANCE_NAME}"
    payload = {
        "number": clean_phone,
        "text": message,
        "delay": 1200,
        "linkPreview": True
    }

    async with httpx.AsyncClient(timeout=25) as client:
        res = await client.post(url, headers=headers, json=payload)
        res.raise_for_status()
        return res.json()


async def send_evolution_media(
    *,
    phone: str,
    media_url: str,
    caption: str,
    media_type: str = "video",
    file_name: str = "mujeeb_outreach.mp4"
) -> dict[str, Any]:
    """Send 20s video demo or media via your private Evolution instance."""
    settings = get_settings()
    base_url = str(settings.evolution_api_url).rstrip("/")
    headers = await get_headers()

    clean_phone = "".join(filter(str.isdigit, phone))
    url = f"{base_url}/message/sendMedia/{INSTANCE_NAME}"
    payload = {
        "number": clean_phone,
        "mediatype": media_type,
        "mimetype": "video/mp4" if media_type == "video" else "image/png",
        "caption": caption,
        "media": media_url,
        "fileName": file_name,
        "delay": 1500
    }

    async with httpx.AsyncClient(timeout=45) as client:
        res = await client.post(url, headers=headers, json=payload)
        res.raise_for_status()
        return res.json()
