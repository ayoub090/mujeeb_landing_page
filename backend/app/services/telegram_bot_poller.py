"""Interactive Telegram Bot listener for Mujeeb Multi-Channel Outreach & Quotas Control.
Provides 1-tap inline buttons, custom quota selection, scraping triggers, and instant status.
"""
import asyncio
import json
import logging
import os
import re
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_dir))

import httpx
from sqlalchemy import func, select

from app.config import get_settings
from app.database import SessionLocal
from app.models import AcquisitionProspect
from app.services.daily_scraper import scrape_and_qualify_stores
from app.services.multi_channel_outreach import dispatch_custom_outreach
from app.services.telegram import send_telegram_notification

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("mujeeb.telegram_poller")

CONFIG_FILE = Path("outreach_quotas_config.json")

DEFAULT_QUOTAS = {
    "wa_limit": 10,
    "email_limit": 30,
    "ig_limit": 10,
    "scrape_limit": 50,
}


def load_quotas() -> dict[str, int]:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return DEFAULT_QUOTAS.copy()


def save_quotas(data: dict[str, int]) -> None:
    CONFIG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


async def send_interactive_menu(chat_id: str, client: httpx.AsyncClient):
    settings = get_settings()
    token = settings.telegram_bot_token
    quotas = load_quotas()

    text = (
        "🤖 <b>CENTRE DE CONTRÔLE OUTREACH & ACQUISITION (MUJEEB)</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 <b>Quotas actuels configurés :</b>\n"
        f"• 🟢 WhatsApp : <b>{quotas.get('wa_limit', 10)}/jour</b>\n"
        f"• ✉️ Emails B2B : <b>{quotas.get('email_limit', 30)}/jour</b>\n"
        f"• 📸 Instagram DMs : <b>{quotas.get('ig_limit', 10)}/jour</b>\n"
        f"• 🕷️ Scraping : <b>{quotas.get('scrape_limit', 50)} boutiques/jour</b>\n\n"
        "👇 <i>Sélectionnez une action rapide ou tapez une commande :</i>"
    )
    keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": f"🚀 Lancer Campagne ({quotas.get('wa_limit', 10)} WA | {quotas.get('email_limit', 30)} Mail | {quotas.get('ig_limit', 10)} DM)",
                    "callback_data": "cmd_launch_default",
                }
            ],
            [
                {"text": f"🕷️ Scraper ({quotas.get('scrape_limit', 50)} boutiques GCC)", "callback_data": "cmd_scrape"},
                {"text": "📊 Statut Base & Canaux", "callback_data": "cmd_status"},
            ],
            [
                {"text": "🟢 QR Code WhatsApp", "callback_data": "cmd_qr"},
                {"text": "📸 Statut Instagram", "callback_data": "cmd_ig_status"},
            ],
            [
                {"text": "⚙️ Quotas : 10 WA / 30 Mail / 10 DM", "callback_data": "cmd_quota_std"},
                {"text": "⚙️ Quotas : 20 WA / 50 Mail / 20 DM", "callback_data": "cmd_quota_boost"},
            ],
        ]
    }
    try:
        await client.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "reply_markup": keyboard,
            },
        )
    except Exception as e:
        logger.error("Error sending interactive menu: %s", e)


async def handle_update(update: dict, client: httpx.AsyncClient):
    settings = get_settings()

    # 1. Handle Callback Queries (Inline Button clicks)
    callback_query = update.get("callback_query")
    if callback_query:
        cq_data = callback_query.get("data")
        cq_id = callback_query.get("id")
        chat_id = str(callback_query.get("message", {}).get("chat", {}).get("id"))

        # Acknowledge callback
        token = settings.telegram_bot_token
        try:
            await client.post(f"https://api.telegram.org/bot{token}/answerCallbackQuery", json={"callback_query_id": cq_id})
        except Exception:
            pass

        if cq_data == "cmd_launch_default":
            quotas = load_quotas()
            asyncio.create_task(dispatch_custom_outreach(
                wa_count=quotas.get("wa_limit", 10),
                email_count=quotas.get("email_limit", 30),
                ig_count=quotas.get("ig_limit", 10),
            ))
        elif cq_data == "cmd_scrape":
            quotas = load_quotas()
            asyncio.create_task(scrape_and_qualify_stores(target_count=quotas.get("scrape_limit", 50)))
        elif cq_data == "cmd_status":
            await show_full_status()
        elif cq_data == "cmd_qr":
            await send_telegram_notification("⏳ <b>Génération du QR Code WhatsApp Baileys...</b>")
            try:
                async with httpx.AsyncClient(timeout=10) as c:
                    r = await c.get("http://baileys:8085/qr")
                    if r.status_code != 200:
                        r = await c.get("http://127.0.0.1:8085/qr")
                    await send_telegram_notification(f"📱 <b>Statut QR :</b> {r.json().get('message')}")
            except Exception as e:
                await send_telegram_notification(f"⚠️ <i>Erreur Baileys : {e}</i>")
        elif cq_data == "cmd_ig_status":
            from app.services.instagram_outreach import is_authenticated as ig_auth, _logged_in_user, _dms_sent_today
            auth = ig_auth()
            ig_msg = (
                "📸 <b>STATUT OUTREACH INSTAGRAM :</b>\n\n"
                f"• Authentifié : <code>{'Oui ✅' if auth else 'Non ❌'}</code>\n"
                f"• Compte : <code>@{_logged_in_user or 'leocreativehub4'}</code>\n"
                f"• DMs envoyés aujourd'hui : <code>{_dms_sent_today}/30</code>\n"
                f"• Moteur : <code>instagrapi (0€ / Mobile API)</code>"
            )
            await send_telegram_notification(ig_msg)
        elif cq_data == "cmd_quota_std":
            save_quotas({"wa_limit": 10, "email_limit": 30, "ig_limit": 10, "scrape_limit": 50})
            await send_telegram_notification("✅ <b>Quotas mis à jour : 10 WA | 30 Mails | 10 DMs | 50 Scrapes</b>")
            await send_interactive_menu(chat_id, client)
        elif cq_data == "cmd_quota_boost":
            save_quotas({"wa_limit": 20, "email_limit": 50, "ig_limit": 20, "scrape_limit": 100})
            await send_telegram_notification("🔥 <b>Quotas Boost activés : 20 WA | 50 Mails | 20 DMs | 100 Scrapes</b>")
            await send_interactive_menu(chat_id, client)
        return

    # 2. Handle Text Commands
    message = update.get("message", {})
    raw_text = (message.get("text") or "").strip()
    text = raw_text.lower()
    chat_id = str(message.get("chat", {}).get("id"))

    if chat_id != str(settings.telegram_chat_id):
        logger.warning("Ignored message from unauthorized chat_id: %s", chat_id)
        return

    logger.info("Received Telegram command: %s", text)

    # Command: / or /menu or /start or /help
    if text in ["/", "/menu", "/start", "/help", "menu", "aide"]:
        await send_interactive_menu(chat_id, client)

    # Command: /launch [wa]wa [mail]mail [dm]dm
    elif text.startswith("/launch") or text.startswith("launch"):
        wa_match = re.search(r'(\d+)\s*wa', text)
        mail_match = re.search(r'(\d+)\s*mail', text)
        dm_match = re.search(r'(\d+)\s*dm', text)

        quotas = load_quotas()
        wa_val = int(wa_match.group(1)) if wa_match else quotas.get("wa_limit", 10)
        mail_val = int(mail_match.group(1)) if mail_match else quotas.get("email_limit", 30)
        dm_val = int(dm_match.group(1)) if dm_match else quotas.get("ig_limit", 10)

        # If user just typed /launch 20
        parts = text.split()
        if len(parts) == 2 and parts[1].isdigit():
            val = int(parts[1])
            wa_val, mail_val, dm_val = val // 3, val // 2, val // 4

        asyncio.create_task(dispatch_custom_outreach(wa_count=wa_val, email_count=mail_val, ig_count=dm_val))

    # Command: /quota wa=10 mail=30 dm=10 scrape=50
    elif text.startswith("/quota") or text.startswith("quota") or text.startswith("/set"):
        quotas = load_quotas()
        for part in text.replace("/quota", "").replace("/set", "").split():
            if "=" in part:
                k, v = part.split("=", 1)
                k = k.strip()
                if v.isdigit():
                    val = int(v)
                    if "wa" in k:
                        quotas["wa_limit"] = val
                    elif "mail" in k or "email" in k:
                        quotas["email_limit"] = val
                    elif "dm" in k or "ig" in k:
                        quotas["ig_limit"] = val
                    elif "scrape" in k or "scrap" in k:
                        quotas["scrape_limit"] = val
        save_quotas(quotas)
        await send_telegram_notification(
            f"✅ <b>Nouveaux Quotas Enregistrés :</b>\n"
            f"• 🟢 WhatsApp : <b>{quotas['wa_limit']}</b>\n"
            f"• ✉️ Emails : <b>{quotas['email_limit']}</b>\n"
            f"• 📸 Instagram DMs : <b>{quotas['ig_limit']}</b>\n"
            f"• 🕷️ Scraping : <b>{quotas['scrape_limit']}</b>"
        )

    # Command: /scrape [count]
    elif text.startswith("/scrape") or text.startswith("scrape"):
        parts = text.split()
        count = int(parts[1]) if len(parts) >= 2 and parts[1].isdigit() else load_quotas().get("scrape_limit", 50)
        asyncio.create_task(scrape_and_qualify_stores(target_count=count))

    # Command: /status
    elif text in ["/status", "status"]:
        await show_full_status()

    # Command: /qr
    elif text in ["/qr", "qr"]:
        try:
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.get("http://baileys:8085/qr")
                if r.status_code != 200:
                    r = await c.get("http://127.0.0.1:8085/qr")
                await send_telegram_notification(f"📱 <b>WhatsApp Baileys :</b> {r.json().get('message')}")
        except Exception as e:
            await send_telegram_notification(f"⚠️ <i>Erreur Baileys : {e}</i>")

    else:
        # Unknown command: show quick menu
        await send_interactive_menu(chat_id, client)


async def show_full_status():
    from app.services.instagram_outreach import is_authenticated as ig_auth, _logged_in_user, _dms_sent_today
    quotas = load_quotas()
    
    # Query DB stats
    async with SessionLocal() as session:
        total = await session.scalar(select(func.count(AcquisitionProspect.id))) or 0
        ready = await session.scalar(select(func.count(AcquisitionProspect.id)).where(AcquisitionProspect.status == "ready")) or 0
        contacted = await session.scalar(select(func.count(AcquisitionProspect.id)).where(AcquisitionProspect.status == "contacted")) or 0

    ig_status = "Connecté ✅" if ig_auth() else "En attente ❌"

    status_card = (
        "📊 <b>ÉTAT DU SYSTÈME D'OUTREACH MULTI-CANAL</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🏬 <b>Base Prospects PostgreSQL :</b>\n"
        f"• 🟢 Prêts à être contactés : <b>{ready} boutiques</b>\n"
        f"• 📩 Déjà contactés : <b>{contacted} boutiques</b>\n"
        f"• 📦 Total en base : <b>{total} boutiques</b>\n\n"
        f"📡 <b>Canaux d'envoi :</b>\n"
        f"• 🟢 <b>WhatsApp (Baileys)</b> : Configuré ({quotas.get('wa_limit', 10)}/j)\n"
        f"• ✉️ <b>Email B2B (Resend)</b> : Opérationnel ({quotas.get('email_limit', 30)}/j)\n"
        f"• 📸 <b>Instagram (@{_logged_in_user or 'leocreativehub4'})</b> : {ig_status} ({quotas.get('ig_limit', 10)}/j)\n\n"
        f"⚡️ <i>Tapez <code>/launch</code> pour lancer l'envoi de la prochaine cohorte.</i>"
    )
    await send_telegram_notification(status_card)


async def start_polling():
    settings = get_settings()
    token = settings.telegram_bot_token
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not configured")
        return

    logger.info("Starting Interactive Telegram Bot Poller on @AyoublidafBot...")
    offset = 0

    async with httpx.AsyncClient(timeout=45) as client:
        # Notify owner that interactive bot is online
        await send_telegram_notification(
            "🤖 <b>BOT INTERACTIF MUJEEB ACTIF & OPÉRATIONNEL !</b>\n\n"
            "Tapez <code>/</code> ou <code>/menu</code> à tout moment pour afficher vos boutons et gérer vos campagnes en direct."
        )

        while True:
            try:
                url = f"https://api.telegram.org/bot{token}/getUpdates?offset={offset}&timeout=30"
                res = await client.get(url)
                if res.status_code == 200:
                    data = res.json()
                    updates = data.get("result", [])
                    for u in updates:
                        offset = max(offset, u.get("update_id", 0) + 1)
                        await handle_update(u, client)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Polling error: %s", e)
                await asyncio.sleep(5)
            await asyncio.sleep(0.5)


if __name__ == "__main__":
    asyncio.run(start_polling())
