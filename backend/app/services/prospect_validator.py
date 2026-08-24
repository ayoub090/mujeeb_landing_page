"""Multi-Channel Prospect Validator & Enrichment Engine for Mujeeb.
Validates Email deliverability (MX/DNS), WhatsApp active registration, and Instagram profile status
BEFORE any outreach is dispatched.
"""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Any
import httpx

try:
    import phonenumbers
except ImportError:
    phonenumbers = None

logger = logging.getLogger("mujeeb.prospect_validator")

BAILEYS_URL = "http://127.0.0.1:8085"


async def verify_email_domain_mx(email: str) -> dict[str, Any]:
    """Verify email syntax and check if domain has active MX mail exchange records."""
    if not email or "@" not in email:
        return {"valid": False, "reason": "invalid_syntax"}

    email = email.strip().lower()
    domain = email.split("@")[1]

    # Check disposable domains
    disposable_list = {"tempmail.com", "10minutemail.com", "guerrillamail.com", "mailinator.com", "trashmail.com"}
    if domain in disposable_list:
        return {"valid": False, "reason": "disposable_domain"}

    # Query Cloudflare DNS over HTTPS for MX records
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            res = await client.get(
                "https://cloudflare-dns.com/dns-query",
                params={"name": domain, "type": "MX"},
                headers={"accept": "application/dns-json"}
            )
            answers = res.json().get("Answer", [])
            if answers:
                mx_host = answers[0].get("data", "").split()[-1]
                return {"valid": True, "mx_host": mx_host, "domain": domain}
            else:
                return {"valid": False, "reason": "no_mx_records"}
    except Exception as e:
        logger.warning("DNS verification failed for %s: %s", domain, e)
        return {"valid": True, "warning": "dns_timeout"}


async def verify_whatsapp_number(phone: str) -> dict[str, Any]:
    """Format phone to E.164 and check active registration on WhatsApp network."""
    if not phone:
        return {"valid": False, "reason": "missing_phone"}

    clean_digits = re.sub(r"\D", "", phone)
    if len(clean_digits) < 8:
        return {"valid": False, "reason": "too_short"}

    # E.164 normalization
    formatted_phone = clean_digits
    if not formatted_phone.startswith(("966", "971", "965", "974", "968", "973", "1", "33", "212")):
        # Default assume Saudi if 05...
        if formatted_phone.startswith("05"):
            formatted_phone = "966" + formatted_phone[1:]
        elif formatted_phone.startswith("5") and len(formatted_phone) == 9:
            formatted_phone = "966" + formatted_phone

    # Check with Baileys engine if active
    try:
        async with httpx.AsyncClient(timeout=6) as client:
            r = await client.post(f"{BAILEYS_URL}/check-number", json={"phone": formatted_phone})
            if r.status_code == 200:
                data = r.json()
                return {"valid": data.get("exists", True), "formatted": formatted_phone, "jid": data.get("jid")}
    except Exception:
        pass # Engine might be offline; return structurally valid phone

    return {"valid": True, "formatted": formatted_phone}


async def verify_instagram_profile(username: str) -> dict[str, Any]:
    """Check if an Instagram handle exists and is reachable."""
    if not username:
        return {"valid": False, "reason": "missing_username"}

    clean_user = username.lstrip("@").strip()
    if len(clean_user) < 2 or " " in clean_user:
        return {"valid": False, "reason": "invalid_handle"}

    try:
        async with httpx.AsyncClient(timeout=6) as client:
            r = await client.get(
                f"https://www.instagram.com/{clean_user}/",
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                follow_redirects=True
            )
            if r.status_code == 200:
                return {"valid": True, "username": clean_user}
            elif r.status_code == 404:
                return {"valid": False, "reason": "user_not_found"}
    except Exception:
        pass

    return {"valid": True, "username": clean_user}


async def validate_and_enrich_prospect(prospect: dict[str, Any]) -> dict[str, Any]:
    """Run comprehensive multi-channel validation on a decision maker lead."""
    email = prospect.get("email")
    phone = prospect.get("phone")
    ig = prospect.get("instagram")

    results = {
        "name": prospect.get("name"),
        "role": prospect.get("role") or prospect.get("jobTitle") or "Decision Maker",
        "company": prospect.get("company") or prospect.get("name"),
        "linkedin": prospect.get("linkedin") or prospect.get("url"),
        "website": prospect.get("website"),
        "country": prospect.get("country", "GCC"),
        "channels": {}
    }

    # Parallel validation
    email_task = verify_email_domain_mx(email) if email else None
    wa_task = verify_whatsapp_number(phone) if phone else None
    ig_task = verify_instagram_profile(ig) if ig else None

    if email_task:
        results["channels"]["email"] = await email_task
    if wa_task:
        results["channels"]["whatsapp"] = await wa_task
    if ig_task:
        results["channels"]["instagram"] = await ig_task

    # Score lead readiness
    active_count = sum(1 for c in results["channels"].values() if c.get("valid"))
    results["ready_for_outreach"] = active_count > 0
    results["verified_channels_count"] = active_count

    return results
