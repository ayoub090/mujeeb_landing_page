import ipaddress

import httpx
from fastapi import HTTPException, status

from app.config import get_settings

ALLOWED_COUNTRIES = {"SA", "AE", "KW", "BH", "QA", "OM"}


async def verify_signup_ip(ip_address: str) -> dict:
    settings = get_settings()
    try:
        address = ipaddress.ip_address(ip_address)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid source IP") from exc

    if address.is_loopback or address.is_private:
        if settings.environment == "production":
            raise HTTPException(status_code=400, detail="Public source IP required")
        return {"allowed": True, "country": "LOCAL", "reason": "development"}

    if not settings.gcc_only_signups:
        return {"allowed": True, "country": None, "reason": "geo restriction disabled"}
    if not settings.maxmind_account_id or not settings.maxmind_license_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Signup verification is temporarily unavailable",
        )

    url = f"https://geoip.maxmind.com/geoip/v2.1/insights/{address.compressed}"
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            response = await client.get(
                url, auth=(settings.maxmind_account_id, settings.maxmind_license_key)
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Signup verification is temporarily unavailable",
        ) from exc

    data = response.json()
    country = data.get("country", {}).get("iso_code")
    traits = data.get("traits", {})
    blocked_trait = any(
        traits.get(flag, False)
        for flag in ("is_anonymous_vpn", "is_public_proxy", "is_hosting_provider", "is_tor_exit_node")
    )
    if blocked_trait:
        raise HTTPException(status_code=403, detail="Anonymous network signups are not supported")
    if country not in ALLOWED_COUNTRIES:
        raise HTTPException(status_code=403, detail="Mujeeb signup is currently limited to GCC countries")
    return {"allowed": True, "country": country}

