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


def address_choice_payload() -> dict:
    return {
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": "Where should we deliver your order? Send your location or type the address."},
            "action": {"buttons": [
                {"type": "reply", "reply": {"id": "send_location", "title": "📍 Send location"}},
                {"type": "reply", "reply": {"id": "type_address", "title": "✍️ Type address"}},
            ]},
        },
    }


def address_confirmation_payload(address: dict) -> dict:
    formatted = address.get("formatted_address") or ", ".join(
        value for value in (address.get("city"), address.get("district"), address.get("street")) if value
    )
    return {
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": f"We will deliver to: {formatted}. Is this correct?"},
            "action": {"buttons": [
                {"type": "reply", "reply": {"id": "confirm_address", "title": "✅ Yes, correct"}},
                {"type": "reply", "reply": {"id": "change_address", "title": "🔄 Change address"}},
            ]},
        },
    }


def upsell_payload(item_name: str = "GCC accessory", price: str = "99") -> dict:
    return {
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": f"Special offer: add {item_name} to your order for only {price} SAR."},
            "action": {"buttons": [
                {"type": "reply", "reply": {"id": "accept_upsell", "title": "➕ Add to order"}},
                {"type": "reply", "reply": {"id": "reject_upsell", "title": "➡️ No thanks"}},
            ]},
        },
    }


def tracking_payload(status: str, tracking_url: str | None = None) -> dict:
    suffix = f" Track it here: {tracking_url}" if tracking_url else ""
    return {"type": "text", "text": {"body": f"Order status: {status or 'in transit'}.{suffix}"}}
