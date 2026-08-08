from __future__ import annotations

from typing import Any

import httpx

from app.config import get_settings


class LLMNotConfigured(RuntimeError):
    """Raised when an automation request is made without an LLM secret."""


async def draft_customer_message(*, order: dict[str, Any], language: str = "ar") -> str:
    settings = get_settings()
    if not settings.openrouter_api_key:
        raise LLMNotConfigured("OpenRouter is not configured")

    system = (
        "You are Mujeeb, a concise GCC COD ecommerce assistant. "
        "Draft one truthful WhatsApp message only. Never invent payment, delivery, "
        "or policy details. Ask the customer to confirm the order or share a precise "
        "delivery location when it is missing. Keep the tone warm and professional."
    )
    user = (
        f"Reply in {language}. Order data (JSON): {order}. "
        "Include the order number and total when present."
    )
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": settings.openrouter_http_referer,
        "X-Title": settings.openrouter_app_name,
    }
    payload = {
        "model": settings.openrouter_model,
        "temperature": 0.2,
        "max_tokens": 300,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
    }
    async with httpx.AsyncClient(timeout=httpx.Timeout(20.0, connect=5.0)) as client:
        response = await client.post(
            f"{str(settings.openrouter_base_url).rstrip('/')}/chat/completions",
            headers=headers,
            json=payload,
        )
    if response.status_code >= 400:
        raise RuntimeError(f"OpenRouter request failed ({response.status_code})")
    data = response.json()
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("OpenRouter returned an invalid completion") from exc
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("OpenRouter returned an empty completion")
    return content.strip()
