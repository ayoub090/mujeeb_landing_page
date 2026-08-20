from html import escape

import httpx

from app.config import get_settings


async def send_telegram_notification(text: str) -> bool:
    """Send an owner notification. Missing credentials never break ingestion."""

    settings = get_settings()
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        return False
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            url,
            json={
                "chat_id": settings.telegram_chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
        )
        response.raise_for_status()
    return True


def prospect_message(*, company: str, website: str, score: int, platform: str | None, country: str | None) -> str:
    return (
        "<b>Nouveau prospect Mujeeb qualifié</b>\n"
        f"Boutique : {escape(company)}\n"
        f"Score : <b>{score}/100</b>\n"
        f"Pays : {escape(country or 'à vérifier')}\n"
        f"Plateforme : {escape(platform or 'à vérifier')}\n"
        f"Site : {escape(website)}\n\n"
        "Statut : en attente de validation. Aucun message n'a été envoyé."
    )
