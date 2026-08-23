"""Interactive Telegram Bot listener for private admin commands (/qr, /status, /outreach).
Runs locally or on VPS to give you instant 1-tap control from your Telegram chat.
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_dir))

import httpx
from app.config import get_settings
from app.services.evolution_outreach import (
    check_instance_connection,
    fetch_and_send_qr_to_telegram,
    init_evolution_instance,
)
from app.services.telegram import send_telegram_notification

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("mujeeb.telegram_poller")


async def handle_update(update: dict, client: httpx.AsyncClient):
    settings = get_settings()
    message = update.get("message", {})
    raw_text = (message.get("text") or "").strip()
    text = raw_text.lower()
    chat_id = str(message.get("chat", {}).get("id"))

    # Security: only process messages from the verified owner chat ID
    if chat_id != str(settings.telegram_chat_id):
        logger.warning("Ignored message from unauthorized chat_id: %s", chat_id)
        return

    logger.info("Received command from owner: %s", text)

    if text in ["/qr", "qr", "/connect", "connect"]:
        await send_telegram_notification("⏳ <b>Génération du QR Code WhatsApp en cours...</b>")
        await init_evolution_instance()
        success = await fetch_and_send_qr_to_telegram()
        if not success:
            conn = await check_instance_connection()
            state = conn.get("instance", {}).get("state")
            if state == "open":
                await send_telegram_notification("✅ <b>Votre WhatsApp est DÉJÀ connecté et actif sur Evolution API !</b>")
            else:
                await send_telegram_notification("⚠️ <i>Impossible de récupérer le QR code. Vérifiez que Evolution API est bien démarré sur le VPS.</i>")

    elif text in ["/status", "status"]:
        conn = await check_instance_connection()
        state = conn.get("instance", {}).get("state", "inconnu")
        status_msg = (
            "📊 <b>STATUT INSTANCE EVOLUTION API PRIVÉE :</b>\n\n"
            f"• État : <code>{state}</code>\n"
            "• Instance : <code>ayoub_outreach</code>\n"
            "• Canal : WhatsApp Baileys (0€)"
        )
        await send_telegram_notification(status_msg)

    elif text in ["/ig_status", "ig_status"]:
        from app.services.instagram_outreach import is_authenticated, _logged_in_user, _dms_sent_today
        auth = is_authenticated()
        ig_msg = (
            "📸 <b>STATUT OUTREACH INSTAGRAM :</b>\n\n"
            f"• Authentifié : <code>{'Oui ✅' if auth else 'Non ❌'}</code>\n"
            f"• Compte : <code>@{_logged_in_user or 'Non configuré'}</code>\n"
            f"• DMs envoyés aujourd'hui : <code>{_dms_sent_today}/30</code>\n"
            f"• Moteur : <code>instagrapi (0€ / Mobile API)</code>\n\n"
            "<i>Pour vous connecter :</i> <code>/ig_login username password [2FA_code]</code>"
        )
        await send_telegram_notification(ig_msg)

    elif text.startswith("/ig_session "):
        from app.services.instagram_outreach import login_instagram_by_sessionid
        parts = raw_text.split(maxsplit=1)
        if len(parts) >= 2:
            sid = parts[1].strip()
            await send_telegram_notification("⏳ <b>Connexion Instagram via cookie de session...</b>")
            res = login_instagram_by_sessionid(sid)
            if res.get("status") == "success":
                await send_telegram_notification(f"🎉 <b>Instagram connecté avec succès pour @{res.get('username')} !</b>")
            else:
                await send_telegram_notification(f"❌ <b>Erreur session :</b> {res.get('error')}")
        else:
            await send_telegram_notification("Syntaxe : <code>/ig_session VOTRE_COOKIE_SESSIONID</code>")

    elif text.startswith("/ig_login "):
        from app.services.instagram_outreach import login_instagram
        parts = raw_text.split()
        if len(parts) >= 3:
            user = parts[1]
            pwd = parts[2]
            code = parts[3] if len(parts) >= 4 else None
            await send_telegram_notification(f"⏳ <b>Connexion Instagram pour @{user}...</b>")
            res = login_instagram(user, pwd, verification_code=code)
            if res.get("status") == "success":
                await send_telegram_notification(f"🎉 <b>Instagram connecté avec succès pour @{user} !</b>")
            elif res.get("status") == "2fa_required":
                await send_telegram_notification(f"🔐 <b>Code 2FA requis !</b> Tapez : <code>/ig_login {user} {pwd} VOTRE_CODE_2FA</code>")
            elif res.get("status") == "challenge_required":
                await send_telegram_notification(f"⚠️ <b>Challenge de sécurité Instagram !</b> Vérifiez vos emails/SMS et réessayez.")
            else:
                await send_telegram_notification(f"❌ <b>Erreur :</b> {res.get('error') or res.get('message')}")
        else:
            await send_telegram_notification("Syntaxe : <code>/ig_login username password [2FA_code]</code>")

    elif text.startswith("/ig_dm "):
        from app.services.instagram_outreach import send_instagram_dm
        parts = raw_text.split(maxsplit=2)
        if len(parts) >= 3:
            target = parts[1]
            dm_content = parts[2]
            await send_telegram_notification(f"⏳ <b>Envoi du DM à @{target} avec délai anti-ban...</b>")
            res = await send_instagram_dm(target_username=target, message=dm_content)
            if res.get("status") == "sent":
                await send_telegram_notification(f"✅ <b>DM envoyé avec succès à @{target} !</b>")
            else:
                await send_telegram_notification(f"❌ <b>Erreur DM :</b> {res.get('error')}")
        else:
            await send_telegram_notification("Syntaxe : <code>/ig_dm target_username Votre message</code>")

    elif text in ["/ig_poll", "ig_poll"]:
        from app.services.instagram_outreach import poll_instagram_replies
        replies = await poll_instagram_replies()
        await send_telegram_notification(f"🔍 <b>Vérification de la boîte IG terminée.</b> {len(replies)} nouvelle(s) réponse(s) détectée(s).")

    elif text in ["/start", "/help", "help"]:
        help_msg = (
            "🤖 <b>CENTRE DE CONTRÔLE OUTREACH PRIVÉ (MUJEEB)</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Voici vos commandes d'administration disponibles :\n\n"
            "🟢 <b>WHATSAPP (BAILEYS) :</b>\n"
            "📲 <b>/qr</b> : Génère le QR Code WhatsApp\n"
            "📊 <b>/status</b> : Statut WhatsApp\n\n"
            "📸 <b>INSTAGRAM (INSTAGRAPI) :</b>\n"
            "📸 <b>/ig_status</b> : Statut du compte Instagram\n"
            "🔑 <b>/ig_login user pass [code]</b> : Connexion Instagram sécurisée\n"
            "💬 <b>/ig_dm user message</b> : Envoyer un DM froid\n"
            "📥 <b>/ig_poll</b> : Vérifier les réponses reçues\n\n"
            "🏓 <b>/ping</b> : Test de réactivité du serveur"
        )
        await send_telegram_notification(help_msg)


async def run_poller():
    settings = get_settings()
    token = settings.telegram_bot_token
    if not token:
        logger.error("No TELEGRAM_BOT_TOKEN found in settings.")
        return

    logger.info("Starting Telegram Poller for @AyoublidafBot...")
    url = f"https://api.telegram.org/bot{token}"
    offset = 0

    async with httpx.AsyncClient(timeout=30) as client:
        # Send a ready message on startup
        ready_msg = (
            "🚀 <b>BOT OUTREACH PRIVÉ EN LIGNE !</b>\n\n"
            "Pour générer le QR Code de connexion WhatsApp à tout moment, tapez simplement :\n"
            "👉 <b>/qr</b>"
        )
        await send_telegram_notification(ready_msg)

        while True:
            try:
                r = await client.get(f"{url}/getUpdates", params={"offset": offset, "timeout": 20})
                if r.status_code == 200:
                    data = r.json()
                    for update in data.get("result", []):
                        offset = update["update_id"] + 1
                        await handle_update(update, client)
                await asyncio.sleep(1)
            except Exception as e:
                logger.error("Poller error: %s", e)
                await asyncio.sleep(3)


if __name__ == "__main__":
    asyncio.run(run_poller())
