"""Dedicated Instagram DM Outreach Engine powered by instagrapi.
Supports session persistence, humanized rate-limiting, and Telegram lead forwarding.
"""
from __future__ import annotations

import asyncio
import logging
import os
import random
from pathlib import Path
from typing import Any

from instagrapi import Client
from instagrapi.exceptions import (
    ChallengeRequired,
    LoginRequired,
    PleaseWaitFewMinutes,
    TwoFactorRequired,
    UserNotFound,
)

from app.config import get_settings
from app.services.telegram import send_telegram_notification

logger = logging.getLogger("mujeeb.instagram_outreach")

SESSION_FILE = Path("instagram_session.json")
_ig_client: Client | None = None
_logged_in_user: str | None = None
_dms_sent_today: int = 0


def get_instagram_client() -> Client:
    global _ig_client
    if _ig_client is None:
        _ig_client = Client()
        _ig_client.delay_range = [3, 7]
        if SESSION_FILE.exists():
            try:
                _ig_client.load_settings(SESSION_FILE)
                logger.info("Loaded Instagram session from %s", SESSION_FILE)
            except Exception as e:
                logger.warning("Could not load session settings: %s", e)
    return _ig_client


def is_authenticated() -> bool:
    client = get_instagram_client()
    try:
        if SESSION_FILE.exists():
            return True
        return client.user_id is not None
    except Exception:
        return False


def login_instagram_by_sessionid(session_id: str) -> dict[str, Any]:
    """Authenticate with Instagram using active browser sessionid cookie (works with Facebook login)."""
    global _logged_in_user
    client = get_instagram_client()

    try:
        clean_sid = session_id.strip().strip('"').strip("'")
        client.login_by_sessionid(clean_sid)
        user_info = client.account_info()
        _logged_in_user = user_info.username
        client.dump_settings(SESSION_FILE)
        logger.info("Instagram session login successful for @%s", _logged_in_user)

        # Notify Telegram
        asyncio.create_task(
            send_telegram_notification(
                f"📸 <b>INSTAGRAM CONNECTÉ (VIA SESSION FB/BROWSER) !</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 <b>Compte</b> : @{_logged_in_user}\n"
                f"⚡️ <i>Moteur prêt pour la prospection DM 0€ !</i>"
            )
        )

        return {"status": "success", "username": _logged_in_user}
    except Exception as e:
        logger.error("Error logging in with sessionid: %s", e)
        return {"status": "error", "error": str(e)}


def login_instagram(
    username: str,
    password: str,
    verification_code: str | None = None
) -> dict[str, Any]:
    """Authenticate with Instagram and persist session to avoid checkpoints."""
    global _logged_in_user
    client = get_instagram_client()

    try:
        if SESSION_FILE.exists():
            try:
                client.load_settings(SESSION_FILE)
                client.login(username, password)
                _logged_in_user = username
                client.dump_settings(SESSION_FILE)
                return {"status": "success", "message": f"Connected as @{username} (from saved session)"}
            except LoginRequired:
                logger.info("Saved session expired, performing fresh login...")

        if verification_code:
            client.login(username, password, verification_code=verification_code)
        else:
            client.login(username, password)

        client.dump_settings(SESSION_FILE)
        _logged_in_user = username
        logger.info("Instagram login successful for @%s", username)

        return {"status": "success", "username": username}

    except TwoFactorRequired:
        return {"status": "2fa_required", "message": "Two-factor authentication code required"}
    except ChallengeRequired:
        return {"status": "challenge_required", "message": "Instagram security challenge required (check your email/SMS)"}
    except PleaseWaitFewMinutes:
        return {"status": "rate_limited", "message": "Instagram requested a few minutes cooldown"}
    except Exception as e:
        logger.error("Instagram login error: %s", e)
        return {"status": "error", "error": str(e)}


async def send_instagram_dm(
    *,
    target_username: str,
    message: str,
    store_name: str | None = None,
    media_path: str | None = None
) -> dict[str, Any]:
    """Send a cold DM to an e-commerce store with humanized delay and Telegram notification."""
    global _dms_sent_today
    client = get_instagram_client()

    clean_target = target_username.lstrip("@").strip()
    logger.info("Resolving Instagram user @%s...", clean_target)

    try:
        user_id = client.user_id_from_username(clean_target)
    except UserNotFound:
        return {"status": "error", "error": f"User @{clean_target} not found"}
    except Exception as e:
        return {"status": "error", "error": f"Failed to resolve user: {e}"}

    # Humanized jitter delay: 35 to 65 seconds
    delay = random.uniform(35, 65)
    logger.info("Applying humanized delay of %.1fs before DM dispatch...", delay)
    await asyncio.sleep(delay)

    try:
        if media_path and os.path.exists(media_path):
            if media_path.endswith((".mp4", ".mov")):
                result = client.direct_send_video(media_path, user_ids=[user_id], text=message)
            else:
                result = client.direct_send_photo(media_path, user_ids=[user_id], text=message)
        else:
            result = client.direct_send(message, user_ids=[user_id])

        _dms_sent_today += 1

        # Notify Telegram
        tg_text = (
            f"📸 <b>INSTAGRAM DM ENVOYÉ !</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🏪 <b>Boutique</b> : {store_name or clean_target}\n"
            f"👤 <b>Compte IG</b> : @{clean_target}\n"
            f"📊 <b>DMs aujourd'hui</b> : {_dms_sent_today}/30\n"
            f"💬 <b>Message</b> :\n<i>{message[:150]}...</i>"
        )
        await send_telegram_notification(tg_text)

        return {"status": "sent", "target": clean_target, "dm_id": str(getattr(result, "id", "sent"))}

    except Exception as e:
        logger.error("Error sending Instagram DM to @%s: %s", clean_target, e)
        return {"status": "error", "error": str(e)}


async def poll_instagram_replies() -> list[dict[str, Any]]:
    """Poll direct threads for replies and forward new inbound messages to Telegram."""
    client = get_instagram_client()
    if not is_authenticated():
        return []

    try:
        threads = client.direct_threads(selected_filter="unread")
        new_replies = []

        for thread in threads:
            for item in thread.messages[:1]:
                if not item.is_sent_by_viewer and item.item_type == "text":
                    reply_text = item.text
                    sender_username = thread.users[0].username if thread.users else "Prospect"

                    # Alert Telegram
                    tg_text = (
                        f"🔥 <b>NOUVELLE RÉPONSE SUR INSTAGRAM !</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"👤 <b>Prospect</b> : @{sender_username}\n"
                        f"💬 <b>Message reçu</b> :\n<blockquote>{reply_text}</blockquote>\n\n"
                        f"👉 <a href='https://instagram.com/{sender_username}'>Répondre sur Instagram</a>"
                    )
                    await send_telegram_notification(tg_text)
                    new_replies.append({"sender": sender_username, "message": reply_text})

        return new_replies

    except Exception as e:
        logger.error("Error polling Instagram replies: %s", e)
        return []
