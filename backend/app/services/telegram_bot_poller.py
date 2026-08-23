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
    text = (message.get("text") or "").strip().lower()
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
        await send_telegram_notification(f"📊 <b>STATUT INSTANCE EVOLUTION API PRIVÉE :</b>

• État : <code>{state}</code>
• Instance : <code>ayoub_outreach</code>")

    elif text in ["/start", "/help", "help"]:
        help_msg = (
            "🤖 <b>CENTRE DE CONTRÔLE OUTREACH PRIVÉ (MUJEEB)</b>
"
            "━━━━━━━━━━━━━━━━━━━━
"
            "Voici vos commandes d'administration disponibles :

"
            "📲 <b>/qr</b> : Génère et envoie immédiatement le QR Code WhatsApp à scanner
"
            "📊 <b>/status</b> : Affiche l'état de connexion de votre instance WhatsApp
"
            "🚀 <b>/ping</b> : Teste la réactivité du serveur Mujeeb"
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
            "🚀 <b>BOT OUTREACH PRIVÉ EN LIGNE !</b>

"
            "Pour générer le QR Code de connexion WhatsApp à tout moment, tapez simplement :
"
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
