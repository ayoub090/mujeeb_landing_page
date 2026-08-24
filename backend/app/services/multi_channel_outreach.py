
"""Unified Multi-Channel Outreach Engine for Mujeeb.
Dispatches outreach simultaneously across:
1. Email (Resend)
2. WhatsApp (Baileys on your US number)
3. Instagram DM (instagrapi on @leocreativehub4)
"""
from __future__ import annotations

import asyncio
import httpx
import json
import logging
import os
import re
from pathlib import Path
from typing import Any


from app.config import get_settings
from app.services.instagram_outreach import is_authenticated, send_instagram_dm
from app.services.telegram import send_telegram_notification

logger = logging.getLogger("mujeeb.multi_channel_outreach")

BAILEYS_URL = "http://127.0.0.1:8085"
VIDEO_URL = "https://usemujeeb.com/videos/video_outreach_20s.mp4"



def build_email_pitch(store_name: str, country: str) -> tuple[str, str]:
    subject = f"⚡️ توفير تكلفة تأكيد الطلبات وتقليل رجوعات الشحن (RTO) لمتجر {store_name}"
    html = f'''
    <div dir="rtl" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 15px; color: #1e293b; line-height: 1.8; max-width: 620px; margin: 0 auto; padding: 20px; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px;">
        <p style="font-size: 16px; margin-top: 0;">السلام عليكم فريق <b>{store_name}</b> 👋</p>
        <p>أتمنى أن تكونوا بخير. اطلعت على متجركم المتميز <b>{store_name}</b> في السوق {country}.</p>
        <p>ندرك جميعاً أن أكبر تحدي يواجه قطاع التجارة الإلكترونية والدفع عند الاستلام (COD) هو <b>تأكيد الطلبات وسحب لوكيشن التوصيل بدقة</b>، حيث تتسبب العناوين النصية غير الدقيقة في ارتفاع نسبة المرتجعات (RTO) وتكاليف الكول سنتر اليدوي.</p>
        <div style="background-color: #f8fafc; border-right: 4px solid #2563eb; padding: 15px; border-radius: 6px; margin: 20px 0;">
            <p style="margin: 0; font-weight: bold; color: #0f172a;">💡 طورنا نظام "مجيب" (Mujeeb AI) لحل هذه المعضلة جذرياً:</p>
            <ul style="margin: 10px 0 0 0; padding-right: 20px; color: #334155;">
                <li><b>تأكيد آلي فوري عبر واتساب</b> فور إتمام الطلب بلهجة خليجية/سعودية طبيعية 100%.</li>
                <li><b>سحب لوكيشن GPS الدقيق بنقرة واحدة</b> وتحويله مباشرة لبوليصة الشحن لتقليل نسبة فشل التوصيل بأكثر من <b>40%</b>.</li>
                <li><b>ربط ومزامنة تلقائية</b> مع متاجر سلة (Salla)، زد (Zid)، وشوبيفاي (Shopify).</li>
            </ul>
        </div>
        <p style="text-align: center; margin: 25px 0;">
            <a href="{VIDEO_URL}" style="background-color: #2563eb; color: #ffffff; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: bold; display: inline-block;">🎥 شاهد فيديو توضيحي للنظام (20 ثانية)</a>
        </p>
        <p>يسعدنا تفعيل <b>تجربة تجريبية مجانية للنظام (Pilot) على متجر {store_name}</b> لمشاهدة الانخفاض المباشر في تكلفة التأكيد ونسبة الرجوعات.</p>
        <p>هل يناسبكم تجربة النظام هذا الأسبوع؟</p>
        <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 25px 0;" />
        <p style="margin-bottom: 0; color: #64748b; font-size: 13px;">
            تحياتي وتقديري،<br>
            <b>أيوب فاضل</b><br>
            فريق منصة مجيب الذكية (Mujeeb)<br>
            🌐 <a href="https://usemujeeb.com" style="color: #2563eb;">usemujeeb.com</a> | ✉️ contact@usemujeeb.com
        </p>
    </div>
    '''
    return subject, html


async def send_whatsapp_message(phone: str, store_name: str) -> bool:
    clean_phone = re.sub(r"\D", "", phone)
    if not clean_phone or len(clean_phone) < 8:
        return False
    if not clean_phone.startswith(("966", "965", "974", "971", "968", "973")):
        if clean_phone.startswith("05"):
            clean_phone = "966" + clean_phone[1:]
        elif clean_phone.startswith("5") and len(clean_phone) == 9:
            clean_phone = "966" + clean_phone
        elif len(clean_phone) == 8:
            clean_phone = "965" + clean_phone

    caption = (
        f"السلام عليكم فريق {store_name} 👋\n\n"
        f"طورنا نظام مجيب (Mujeeb AI) لأتمتة تأكيد طلبات الدفع عند الاستلام (COD) وسحب لوكيشن GPS للعميل آلياً عبر واتساب لتقليل الرجوعات بنسبة 40% وتوفير تكاليف الاتصال اليدوي.\n\n"
        f"🎥 فيديو سريع 20 ثانية يوضح الآلية: {VIDEO_URL}\n\n"
        f"يسعدنا تفعيل تجربة مجانية لمتجركم 🤝"
    )
    payload = {"phone": clean_phone, "mediaUrl": VIDEO_URL, "caption": caption, "mediaType": "video"}
    try:
        async with httpx.AsyncClient(timeout=25) as client:
            res = await client.post(f"{BAILEYS_URL}/send-media", json=payload)
            return res.status_code == 200
    except Exception as e:
        logger.warning("WhatsApp send error for %s: %s", clean_phone, e)
        return False


async def send_instagram_outreach(ig_handle: str, store_name: str) -> bool:
    try:
        clean_handle = ig_handle.replace(".com.kw", "").replace(".com", "").replace(".net", "").replace(".me", "").replace(".shop", "").replace(".qa", "").replace(".sa", "").strip()
        if is_authenticated() and clean_handle and len(clean_handle) > 2:
            msg = (
                f"مرحباً فريق {store_name} 👋\n\n"
                f"نقدم لكم نظام مجيب (Mujeeb) لأتمتة تأكيد طلبات الدفع عند الاستلام وسحب لوكيشن GPS آلياً لتفادي الرجوعات وتوفير تكاليف الكول سنتر.\n\n"
                f"🎥 فيديو توضيحي 20 ثانية: {VIDEO_URL}\n\n"
                f"يسعدنا تقديم تجربة مجانية لمتجركم 🤝"
            )
            res = await send_instagram_dm(target_username=clean_handle, message=msg, store_name=store_name)
            return res.get("status") == "sent"
    except Exception as e:
        logger.warning("IG send error for @%s: %s", ig_handle, e)
    return False


async def dispatch_multi_channel_store(client: httpx.AsyncClient, store: dict[str, Any], index: int, total: int) -> bool:
    name = store.get("store_name") or store.get("name")
    email = store.get("email")
    phone = store.get("phone")
    ig = store.get("instagram") or store.get("domain")
    country = store.get("country", "الخليج")

    channels_activated = []

    settings = get_settings()
    resend_key = settings.resend_api_key or os.getenv("RESEND_API_KEY")

    # 1. Email (Resend)
    if email and store.get("has_mx", True) and resend_key:
        subject, html = build_email_pitch(name, country)
        headers = {"Authorization": f"Bearer {resend_key}", "Content-Type": "application/json"}
        payload = {
            "from": "Ayoub - Mujeeb <contact@usemujeeb.com>",
            "to": [email],
            "reply_to": "contact@usemujeeb.com",
            "subject": subject,
            "html": html,
        }
        try:
            r = await client.post("https://api.resend.com/emails", headers=headers, json=payload, timeout=12)
            if r.status_code == 200:
                channels_activated.append("📧 Email (Resend)")
        except Exception:
            pass

    # 2. WhatsApp (Baileys)
    if phone:
        ok_wa = await send_whatsapp_message(phone, name)
        if ok_wa:
            channels_activated.append("🟢 WhatsApp (Baileys)")

    # 3. Instagram DM (instagrapi)
    if ig:
        ok_ig = await send_instagram_outreach(ig, name)
        if ok_ig:
            channels_activated.append("📸 Instagram DM")

    channels_str = " + ".join(channels_activated) if channels_activated else "En attente"
    logger.info("[%d/%d] Outreach dispatched for %s via: %s", index, total, name, channels_str)

    tg_card = (
        f"🚀 <b>OUTREACH TRIPLE TOUCHPOINT EXPÉDIÉ !</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏪 <b>Boutique</b> : {name}\n"
        f"📍 <b>Marché</b> : {country}\n"
        f"📡 <b>Canaux Activés</b> : <b>{channels_str}</b>\n"
        f"📊 <b>Progression</b> : [{index}/{total}]"
    )
    await send_telegram_notification(tg_card)
    return len(channels_activated) > 0


async def run_daily_multi_channel_campaign(limit: int = 25) -> dict[str, Any]:
    """Execute the full daily multi-channel campaign across WhatsApp, Instagram, and Email."""
    data_file = Path("real_30_target_stores.json")
    if not data_file.exists():
        data_file = Path("../real_30_target_stores.json")

    with open(data_file, "r", encoding="utf-8") as f:
        stores = json.load(f)

    target_stores = stores[:limit]
    logger.info("Starting full daily multi-channel campaign for %d stores...", len(target_stores))

    await send_telegram_notification(
        f"🔥 <b>DÉMARRAGE DE LA CAMPAGNE MULTI-CANAL QUOTIDIENNE ({len(target_stores)} BOUTIQUES) !</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📡 <b>Canaux synchronisés</b> : 📧 Email (Resend) + 🟢 WhatsApp (Baileys) + 📸 Instagram (instagrapi)\n"
        f"⚡️ <i>Outreach 100% sans frais tiers en cours d'exécution...</i>"
    )

    success_count = 0
    async with httpx.AsyncClient(timeout=15) as client:
        for i, s in enumerate(target_stores, start=1):
            ok = await dispatch_multi_channel_store(client, s, i, len(target_stores))
            if ok:
                success_count += 1
            # Humanized anti-ban delay: 25 to 40 seconds
            await asyncio.sleep(random.uniform(25, 40))

    await send_telegram_notification(
        f"🏁 <b>CAMPAGNE QUOTIDIENNE MULTI-CANAL TERMINÉE !</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ <b>Boutiques contactées avec succès</b> : {success_count}/{len(target_stores)}\n"
        f"📥 <i>Toutes les réponses des marchands vous seront transmises en direct !</i>"
    )
    logger.info("Daily multi-channel campaign completed successfully!")
    return {"status": "completed", "success": success_count, "total": len(target_stores)}

