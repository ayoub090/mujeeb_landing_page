"""Unified Multi-Channel Outreach Engine for Mujeeb.
Dispatches outreach simultaneously across:
1. WhatsApp (Baileys Engine + Demo Video)
2. Email (Resend API + RTL HTML + Video CTA)
3. Instagram DM (Instagrapi + Video Link)
Supports customizable per-channel quotas (e.g. 10 WA, 30 Email, 10 DM).
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import random
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy import select

from app.config import get_settings
from app.database import SessionLocal
from app.models import AcquisitionProspect
from app.services.instagram_outreach import is_authenticated, send_instagram_dm
from app.services.telegram import send_telegram_notification

logger = logging.getLogger("mujeeb.multi_channel_outreach")

BAILEYS_URL = os.getenv("BAILEYS_URL", "http://baileys:8085")
VIDEO_URL = "https://usemujeeb.com/videos/video_outreach_20s.mp4"


def build_email_pitch(store_name: str, country: str = "السعودية") -> tuple[str, str]:
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


async def send_whatsapp_baileys(phone: str, store_name: str, message: str | None = None) -> bool:
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

    caption = message or (
        f"السلام عليكم فريق {store_name} 👋\n\n"
        f"طورنا نظام مجيب (Mujeeb AI) لأتمتة تأكيد طلبات الدفع عند الاستلام (COD) وسحب لوكيشن GPS للعميل آلياً عبر واتساب لتقليل الرجوعات بنسبة 40% وتوفير تكاليف الاتصال اليدوي.\n\n"
        f"🎥 فيديو سريع 20 ثانية يوضح الآلية: {VIDEO_URL}\n\n"
        f"يسعدنا تفعيل تجربة مجانية لمتجركم 🤝"
    )
    payload = {"phone": clean_phone, "mediaUrl": VIDEO_URL, "caption": caption, "mediaType": "video"}
    
    urls_to_try = [BAILEYS_URL, "http://baileys:8085", "http://127.0.0.1:8085"]
    for b_url in urls_to_try:
        try:
            async with httpx.AsyncClient(timeout=25) as client:
                res = await client.post(f"{b_url}/send-media", json=payload)
                if res.status_code == 200:
                    return True
        except Exception:
            pass
    return False


async def send_email_resend(email: str, store_name: str, country: str = "SA") -> bool:
    settings = get_settings()
    resend_key = settings.resend_api_key or os.getenv("RESEND_API_KEY", "")
    from_email = settings.resend_from_email or os.getenv("RESEND_FROM_EMAIL", "contact@usemujeeb.com")
    if not resend_key or not email:
        return False
    
    subject, html = build_email_pitch(store_name, country)
    headers = {"Authorization": f"Bearer {resend_key}", "Content-Type": "application/json"}
    payload = {
        "from": f"Ayoub - Mujeeb <{from_email}>",
        "to": [email],
        "reply_to": "contact@usemujeeb.com",
        "subject": subject,
        "html": html,
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post("https://api.resend.com/emails", headers=headers, json=payload)
            return r.status_code in (200, 201)
    except Exception as e:
        logger.warning("Resend email failed for %s: %s", email, e)
    return False


async def send_instagram_dm_outreach(ig_handle: str, store_name: str) -> bool:
    try:
        clean_handle = ig_handle.replace(".com.kw", "").replace(".com", "").replace(".net", "").replace(".me", "").replace(".shop", "").replace(".qa", "").replace(".sa", "").strip()
        if clean_handle and len(clean_handle) > 2:
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


async def dispatch_custom_outreach(
    wa_count: int = 10,
    email_count: int = 30,
    ig_count: int = 10,
) -> dict[str, Any]:
    """Execute customizable multi-channel outreach cohort across WhatsApp, Email and Instagram DMs."""
    logger.info("Launching custom multi-channel outreach: %d WA, %d Email, %d IG", wa_count, email_count, ig_count)
    
    total_target = wa_count + email_count + ig_count
    await send_telegram_notification(
        f"🚀 <b>DÉMARRAGE CAMPAGNE MULTI-CANAL PERSONNALISÉE</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 <b>Quotas choisis</b> :\n"
        f"• 🟢 WhatsApp (Baileys) : <b>{wa_count}</b>\n"
        f"• ✉️ Emails B2B (Resend) : <b>{email_count}</b>\n"
        f"• 📸 Instagram DMs : <b>{ig_count}</b>\n"
        f"• 📊 Total visé : <b>{total_target} boutiques</b>\n\n"
        f"⚡️ <i>Exécution et respect des délais anti-ban en cours...</i>"
    )

    sent_wa = 0
    sent_email = 0
    sent_ig = 0
    contacted_ids = set()

    async with SessionLocal() as session:
        # 1. Dispatch WhatsApp (top prospects with phone)
        if wa_count > 0:
            query_wa = select(AcquisitionProspect).where(
                AcquisitionProspect.status.in_(["ready", "new", "qualified"]),
                AcquisitionProspect.public_phone.is_not(None),
                AcquisitionProspect.id.notin_(contacted_ids) if contacted_ids else True,
            ).order_by(AcquisitionProspect.score.desc()).limit(wa_count)
            
            wa_prospects = list((await session.scalars(query_wa)).all())
            for p in wa_prospects:
                ok = await send_whatsapp_baileys(p.public_phone, p.company, p.message_draft)
                if ok:
                    sent_wa += 1
                    p.status = "contacted"
                    p.outreach_channel = "whatsapp_baileys"
                    p.last_contacted_at = datetime.now(UTC)
                    p.contact_attempts = (p.contact_attempts or 0) + 1
                    contacted_ids.add(p.id)
                    await session.commit()
                await asyncio.sleep(random.uniform(2, 5))

        # 2. Dispatch Email (top prospects with email)
        if email_count > 0:
            query_mail = select(AcquisitionProspect).where(
                AcquisitionProspect.status.in_(["ready", "new", "qualified"]),
                AcquisitionProspect.public_email.is_not(None),
                AcquisitionProspect.id.notin_(contacted_ids) if contacted_ids else True,
            ).order_by(AcquisitionProspect.score.desc()).limit(email_count)
            
            mail_prospects = list((await session.scalars(query_mail)).all())
            for p in mail_prospects:
                ok = await send_email_resend(p.public_email, p.company, p.country_code or "SA")
                if ok:
                    sent_email += 1
                    p.status = "contacted"
                    p.outreach_channel = "business_email"
                    p.last_contacted_at = datetime.now(UTC)
                    p.contact_attempts = (p.contact_attempts or 0) + 1
                    contacted_ids.add(p.id)
                    await session.commit()
                await asyncio.sleep(1)

        # 3. Dispatch Instagram DM (top prospects with instagram handle)
        if ig_count > 0:
            query_ig = select(AcquisitionProspect).where(
                AcquisitionProspect.status.in_(["ready", "new", "qualified"]),
                AcquisitionProspect.id.notin_(contacted_ids) if contacted_ids else True,
            ).order_by(AcquisitionProspect.score.desc()).limit(ig_count * 2)
            
            ig_prospects = list((await session.scalars(query_ig)).all())
            for p in ig_prospects:
                if sent_ig >= ig_count:
                    break
                handle = (p.social_profiles or {}).get("instagram") or p.canonical_website.replace("https://", "").replace("http://", "").split("/")[0].split(".")[0]
                ok = await send_instagram_dm_outreach(handle, p.company)
                if ok:
                    sent_ig += 1
                    p.status = "contacted"
                    p.outreach_channel = "instagram_dm"
                    p.last_contacted_at = datetime.now(UTC)
                    p.contact_attempts = (p.contact_attempts or 0) + 1
                    contacted_ids.add(p.id)
                    await session.commit()
                    await asyncio.sleep(random.uniform(15, 30))

    # Send Final Detailed Report to Telegram
    total_contacted = sent_wa + sent_email + sent_ig
    summary_report = (
        f"🎯 <b>RAPPORT DE PROSPECTION MULTI-CANAL TERMINÉ !</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🟢 <b>WhatsApp (Baileys)</b> : <b>{sent_wa}/{wa_count}</b>\n"
        f"✉️ <b>Emails B2B (Resend)</b> : <b>{sent_email}/{email_count}</b>\n"
        f"📸 <b>Instagram DMs (Instagrapi)</b> : <b>{sent_ig}/{ig_count}</b>\n"
        f"📊 <b>Total nouveaux marchands contactés</b> : <b>{total_contacted}/{total_target}</b>\n\n"
        f"⚡️ <i>Automatisation 100% opérationnelle. Les réponses apparaîtront en direct ici !</i>"
    )
    await send_telegram_notification(summary_report)
    logger.info("Outreach completed. WA: %d, Email: %d, IG: %d, Total: %d", sent_wa, sent_email, sent_ig, total_contacted)
    return {
        "status": "completed",
        "sent_wa": sent_wa,
        "sent_email": sent_email,
        "sent_ig": sent_ig,
        "total_contacted": total_contacted,
        "target": total_target,
    }
