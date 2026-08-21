import asyncio
import os
import sys
import time
from datetime import UTC, datetime
from typing import Any
import httpx

from app.config import get_settings
from app.models import AcquisitionProspect
from app.services.telegram import send_telegram_notification


async def send_whatsapp_via_waapi(
    *,
    instance_id: str,
    api_token: str,
    phone_number: str,
    message: str,
    base_url: str = "https://waapi.app/api/v1"
) -> dict[str, Any]:
    """Send a direct 1-to-1 WhatsApp message via WaAPI instance."""
    clean_phone = "".join(filter(str.isdigit, phone_number))
    chat_id = f"{clean_phone}@c.us"
    
    url = f"{base_url.rstrip('/')}/instances/{instance_id}/client/action/send-message"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {
        "chatId": chat_id,
        "message": message
    }
    
    async with httpx.AsyncClient(timeout=30) as client:
        res = await client.post(url, headers=headers, json=payload)
        res.raise_for_status()
        return res.json()


async def send_whatsapp_media_via_waapi(
    *,
    instance_id: str,
    api_token: str,
    phone_number: str,
    media_url: str,
    caption: str,
    base_url: str = "https://waapi.app/api/v1"
) -> dict[str, Any]:
    """Send a video demo or media attachment via WhatsApp with personalized caption."""
    clean_phone = "".join(filter(str.isdigit, phone_number))
    chat_id = f"{clean_phone}@c.us"
    
    url = f"{base_url.rstrip('/')}/instances/{instance_id}/client/action/send-media"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {
        "chatId": chat_id,
        "mediaUrl": media_url,
        "mediaCaption": caption
    }
    
    async with httpx.AsyncClient(timeout=45) as client:
        res = await client.post(url, headers=headers, json=payload)
        res.raise_for_status()
        return res.json()


async def send_email_via_resend(
    *,
    api_key: str,
    from_email: str,
    to_email: str,
    subject: str,
    body_text: str,
    from_name: str = "Mujeeb"
) -> dict[str, Any]:
    """Send a personalized B2B outreach email via Resend API."""
    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    html_body = f"""
    <div dir="rtl" style="font-family: Arial, sans-serif; line-height: 1.8; color: #172033; max-width: 600px; margin: auto; padding: 20px;">
        <p style="white-space: pre-wrap;">{body_text}</p>
        <div style="margin: 25px 0; text-align: center;">
            <a href="https://usemujeeb.com/#book" style="background-color: #0f172a; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">
                مشاهدة فيديو تجربة النظام (15 ثانية) 🎬
            </a>
        </div>
        <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;">
        <p style="font-size: 12px; color: #64748b;">مجيب (Mujeeb) — منصة تأكيد طلبات الدفع عند الاستلام للمتاجر الإلكترونية</p>
    </div>
    """
    payload = {
        "from": f"{from_name} <{from_email}>",
        "to": [to_email],
        "subject": subject,
        "text": body_text,
        "html": html_body
    }
    
    async with httpx.AsyncClient(timeout=20) as client:
        res = await client.post(url, headers=headers, json=payload)
        res.raise_for_status()
        return res.json()
