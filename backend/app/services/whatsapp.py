from __future__ import annotations

import httpx

from app.config import get_settings


async def send_whatsapp_message(to: str, body: dict) -> dict:
    settings = get_settings()
    if not settings.meta_access_token or not settings.meta_phone_number_id:
        return {"sent": False, "reason": "whatsapp_credentials_missing"}
    url = f"https://graph.facebook.com/{settings.meta_graph_version}/{settings.meta_phone_number_id}/messages"
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            url,
            headers={"Authorization": f"Bearer {settings.meta_access_token}"},
            json={"messaging_product": "whatsapp", "to": to, **body},
        )
        response.raise_for_status()
        return {"sent": True, **response.json()}


def confirmation_payload(order_number: str, amount: str, customer_name: str) -> dict:
    return {
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": f"Ahlan {customer_name}! Confirm order #{order_number} for {amount} SAR?"},
            "action": {"buttons": [
                {"type": "reply", "reply": {"id": "confirm_order", "title": "✅ Confirm Order"}},
                {"type": "reply", "reply": {"id": "cancel_order", "title": "❌ Cancel Order"}},
                {"type": "reply", "reply": {"id": "modify_order", "title": "✏️ Modify Order"}},
            ]},
        },
    }
