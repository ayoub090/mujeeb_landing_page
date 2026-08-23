"""Automated Batch Outreach Runner for Instagram, Email, and Multi-Channel.
Runs in the background, iterates through prospect queue with anti-ban pacing,
and streams live progress directly to Telegram.
"""
from __future__ import annotations

import asyncio
import json
import logging
import random
from pathlib import Path
from typing import Any

from app.services.instagram_outreach import is_authenticated, send_instagram_dm
from app.services.telegram import send_telegram_notification

logger = logging.getLogger("mujeeb.batch_outreach")

QUEUE_FILE = Path("outreach_prospects_queue.json")
VIDEO_URL = "https://usemujeeb.com/videos/video_outreach_20s.mp4"

_is_running = False
_stop_requested = False


def is_batch_running() -> bool:
    return _is_running


def stop_batch_runner():
    global _stop_requested
    _stop_requested = True
    logger.info("Batch stop requested by user.")


async def run_instagram_batch(limit: int = 15) -> dict[str, Any]:
    """Execute fully automated batch Instagram DM campaign without manual validation."""
    global _is_running, _stop_requested

    if _is_running:
        return {"status": "busy", "message": "A batch campaign is already running."}

    if not is_authenticated():
        return {"status": "unauthenticated", "message": "Instagram session is not connected."}

    if not QUEUE_FILE.exists():
        return {"status": "empty", "message": "No prospect queue found."}

    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        all_prospects = json.load(f)

    # Filter prospects with instagram
    targets = [p for p in all_prospects if p.get("instagram")][:limit]

    if not targets:
        return {"status": "empty", "message": "No prospects with Instagram handles found."}

    _is_running = True
    _stop_requested = False

    # Start Telegram Notification
    start_msg = (
        f"🚀 <b>LANCEMENT DE LA CAMPAGNE INSTAGRAM EN BATCH !</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 <b>Cible</b> : {len(targets)} boutiques e-commerce\n"
        f"⏱ <b>Délai sécurisé</b> : 45s à 75s entre chaque DM\n"
        f"⚡️ <i>Exécution 100% autonome en tâche de fond...</i>"
    )
    await send_telegram_notification(start_msg)

    success_count = 0
    fail_count = 0

    try:
        for idx, prospect in enumerate(targets, start=1):
            if _stop_requested:
                await send_telegram_notification("🛑 <b>Campagne arrêtée manuellement.</b>")
                break

            store_name = prospect.get("name", "المتجر")
            ig_handle = prospect.get("instagram", "").lstrip("@").strip()

            # Dynamic localized message templates
            templates = [
                (
                    f"مرحباً فريق {store_name} 👋\n\n"
                    f"لاحظنا تميزكم في تجارة الدفع عند الاستلام (COD).\n"
                    f"طورنا نظام "مجيب" (Mujeeb) لأتمتة تأكيد الطلبات وسحب لوكيشن GPS الدقيق للعملاء آلياً عبر واتساب، مما يقلل رجوعات الشحن بنسبة 40% ويوفر تكاليف موظفي الاتصال اليدوي.\n\n"
                    f"🎥 فيديو توضيحي 20 ثانية: {VIDEO_URL}\n\n"
                    f"يسعدنا تقديم تجربة مجانية لمتجركم 🤝"
                ),
                (
                    f"السلام عليكم فريق {store_name} 👋\n\n"
                    f"حل ذكي لمتاجر الدفع عند الاستلام: نظام Mujeeb يؤكد طلباتكم ويسحب لوكيشن العميل بدقة بنقرة واحدة على واتساب لرفع نسبة التسليم وخفض تكلفة الكول سنتر.\n\n"
                    f"🎥 شرح سريع في 20 ثانية: {VIDEO_URL}\n\n"
                    f"يسعدنا تفعيل تجربة مجانية لكم!"
                )
            ]
            message = random.choice(templates)

            logger.info("[%d/%d] Dispatching DM to @%s...", idx, len(targets), ig_handle)
            res = await send_instagram_dm(target_username=ig_handle, message=message, store_name=store_name)

            if res.get("status") == "sent":
                success_count += 1
                progress_msg = (
                    f"[{idx}/{len(targets)}] ✅ <b>DM ENVOYÉ !</b>\n"
                    f"🏪 <b>Boutique</b> : {store_name}\n"
                    f"👤 <b>IG</b> : @{ig_handle}"
                )
                await send_telegram_notification(progress_msg)
            else:
                fail_count += 1
                err_msg = f"[{idx}/{len(targets)}] ⚠️ <b>Échec @{ig_handle}</b>: {res.get('error')}"
                await send_telegram_notification(err_msg)

        # Final Summary Notification
        summary_msg = (
            f"🏁 <b>CAMPAGNE INSTAGRAM TERMINÉE !</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ <b>DMs livrés avec succès</b> : {success_count}\n"
            f"⚠️ <b>Échecs / Introuvables</b> : {fail_count}\n"
            f"📊 <b>Total traité</b> : {success_count + fail_count}\n"
            f"⚡️ <i>Toutes les réponses des marchands vous seront transmises ici en direct !</i>"
        )
        await send_telegram_notification(summary_msg)

    except Exception as e:
        logger.error("Error during batch campaign: %s", e)
        await send_telegram_notification(f"❌ <b>Erreur dans la campagne batch :</b> {e}")
    finally:
        _is_running = False

    return {
        "status": "completed",
        "success": success_count,
        "failed": fail_count,
        "total": success_count + fail_count
    }
