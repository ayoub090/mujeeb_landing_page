"""Dedicated Instagram DM Outreach Engine powered by okgram.
Supports session persistence, TOTP/SMS 2FA handling, humanized rate-limiting, and Telegram lead forwarding.
"""
from __future__ import annotations

import asyncio
import logging
import os
import random
from pathlib import Path
from typing import Any

from okgram import InstagramAPI

from app.services.telegram import send_telegram_notification

logger = logging.getLogger("mujeeb.instagram_outreach")

SESSION_FILE = Path("/app/data/instagram_session.json")
_ig_client: InstagramAPI | None = None
_logged_in_user: str | None = None
_dms_sent_today: int = 0


def get_instagram_client() -> InstagramAPI:
    global _ig_client
    if _ig_client is None:
        _ig_client = InstagramAPI(
            device_seed="mujeeb_outreach",
            delay_range=(1.0, 3.0),
        )
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


def login_instagram(
    username: str,
    password: str,
    verification_code: str | None = None
) -> dict[str, Any]:
    """Authenticate with Instagram with full support for TOTP / SMS 2FA."""
    global _logged_in_user, _ig_client
    client = get_instagram_client()

    clean_user = username.strip().lstrip("@")
    clean_code = str(verification_code).strip() if verification_code else ""

    try:
        if clean_code:
            logger.info("Attempting 2FA login for @%s with verification code...", clean_user)
            # Try login with code
            client.login(clean_user, password, verification_code=clean_code)
        else:
            logger.info("Attempting initial login for @%s...", clean_user)
            client.login(clean_user, password)

        # CRUCIAL: aligns geo, pulls live config, warms up
        try:
            client.bootstrap()
        except Exception as e:
            logger.warning("Bootstrap failed (may not be an issue if session is restored): %s", e)

        # Successful login
        _logged_in_user = clean_user
        SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
        client.dump_settings(SESSION_FILE)
        logger.info("Instagram login SUCCESS for @%s", clean_user)

        # Notify Telegram
        asyncio.create_task(
            send_telegram_notification(
                f"🎉 <b>INSTAGRAM CONNECTÉ AVEC SUCCÈS !</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 <b>Compte</b> : @{clean_user}\n"
                f"📱 <b>Appareil</b> : Mobile Android (Session Active)\n"
                f"⚡️ <i>Moteur prêt pour la prospection DM 0€ !</i>"
            )
        )

        return {"status": "success", "username": clean_user}

    except Exception as e:
        err_name = type(e).__name__
        if "TwoFactor" in err_name:
            last_json = getattr(client, "last_json", {}) or {}
            tf_info = last_json.get("two_factor_info", {})
            is_totp = tf_info.get("totp_two_factor_on", True)
            msg_type = "Authenticator App (Google/MS Authenticator)" if is_totp else "SMS"
            logger.info("2FA required for @%s (Type: %s)", clean_user, msg_type)
            return {
                "status": "2fa_required",
                "message": f"Code 2FA requis ({msg_type})",
                "is_totp": is_totp
            }
        elif "BadPassword" in err_name:
            return {"status": "error", "error": "Mot de passe incorrect."}
        elif "ChallengeRequired" in err_name:
            return {"status": "challenge_required", "message": "Challenge de sécurité requis par Instagram (vérifiez vos emails)."}
        elif "PleaseWaitFewMinutes" in err_name or "rate_limit" in str(e).lower():
            return {"status": "rate_limited", "message": "Instagram demande de patienter quelques minutes."}
        else:
            logger.error("Instagram login error: %s", e)
            return {"status": "error", "error": str(e)}


def login_instagram_by_sessionid(session_id: str) -> dict[str, Any]:
    """Authenticate with Instagram using a raw sessionid cookie."""
    global _logged_in_user, _ig_client
    client = get_instagram_client()
    try:
        client.login_by_sessionid(session_id.strip())
        _logged_in_user = "session_user"
        SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
        client.dump_settings(SESSION_FILE)
        return {"status": "success", "username": "authenticated_user"}
    except Exception as e:
        logger.error("Sessionid login error: %s", e)
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

    user_id = None
    try:
        # 1. Try native v1 mobile endpoint
        if hasattr(client, "user_info_by_username_v1"):
            info = client.user_info_by_username_v1(clean_target)
        else:
            info = client.user_info_by_username(clean_target)
        user_id = info.pk
    except Exception:
        try:
            # 2. Try search API fallback
            users = client.search_users(clean_target)
            for u in users:
                if u.username.lower() == clean_target.lower():
                    user_id = u.pk
                    break
        except Exception as e:
            return {"status": "error", "error": f"Failed to resolve user @{clean_target}: {e}"}

    if not user_id:
        return {"status": "error", "error": f"User @{clean_target} not found on Instagram"}

    # Humanized jitter delay: 40 to 70 seconds
    delay = random.uniform(40, 70)
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
