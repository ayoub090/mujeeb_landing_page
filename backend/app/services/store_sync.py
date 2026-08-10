from __future__ import annotations

import hashlib
import hmac

import httpx

from app.config import get_settings
from app.models import Order


async def sync_order_to_store(order: Order, event: str) -> dict:
    """Send one canonical mutation event to n8n/store adapters.

    The adapter is optional: without a configured n8n URL the internal order
    remains authoritative and the result explicitly reports that no external
    transport was configured.
    """
    settings = get_settings()
    payload = {
        "event": event,
        "store_id": str(order.store_id),
        "order_id": str(order.id),
        "external_order_id": order.external_order_id,
        "status": order.status.value,
        "amount": str(order.amount),
        "currency": order.currency,
        "address": order.address_data,
        "llm_decision": order.llm_decision,
        "tracking_number": order.tracking_number,
        "carrier_name": order.carrier_name,
        "items": order.items,
        "internal_tags": ["WA_Confirmed_Address_Verified"] if event == "FINAL_STORE_SYNC" else [],
        "order_note": (
            f"Google Maps: https://maps.google.com/?q={order.gps_lat},{order.gps_lng}"
            if order.gps_lat is not None and order.gps_lng is not None else None
        ),
    }
    if not settings.n8n_webhook_url:
        return {"synced": False, "reason": "store_adapter_not_configured", "payload": payload}
    raw = str(payload).encode()
    signature = hmac.new(settings.n8n_shared_secret.encode(), raw, hashlib.sha256).hexdigest() if settings.n8n_shared_secret else ""
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(settings.n8n_webhook_url, json=payload, headers={"X-Mujeeb-Signature": signature})
        response.raise_for_status()
    return {"synced": True, "status_code": response.status_code}
