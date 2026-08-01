import hashlib
import time

import httpx

from app.config import get_settings


def _hash(value: str) -> str:
    return hashlib.sha256(value.strip().lower().encode()).hexdigest()


async def send_capi_event(
    event_name: str,
    event_id: str,
    *,
    email: str | None = None,
    phone: str | None = None,
    client_ip: str | None = None,
    user_agent: str | None = None,
    value: float = 0,
    currency: str = "SAR",
) -> None:
    settings = get_settings()
    if not settings.meta_pixel_id or not settings.meta_capi_access_token:
        return
    user_data: dict[str, object] = {}
    if email:
        user_data["em"] = [_hash(email)]
    if phone:
        user_data["ph"] = [_hash(phone)]
    if client_ip:
        user_data["client_ip_address"] = client_ip
    if user_agent:
        user_data["client_user_agent"] = user_agent
    payload = {
        "data": [{
            "event_name": event_name,
            "event_time": int(time.time()),
            "event_id": event_id,
            "action_source": "website",
            "event_source_url": "https://usemujeeb.com/",
            "user_data": user_data,
            "custom_data": {"value": value, "currency": currency},
        }],
        "access_token": settings.meta_capi_access_token,
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"https://graph.facebook.com/{settings.meta_graph_version}/{settings.meta_pixel_id}/events",
                json=payload,
            )
            response.raise_for_status()
    except httpx.HTTPError:
        return
