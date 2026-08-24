import asyncio
import logging
import os
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from app.config import get_settings
from app.database import SessionLocal
from app.models import AcquisitionProspect
from app.services.telegram import send_telegram_notification
from app.services.automated_outreach import send_whatsapp_via_waapi, send_email_via_resend

logger = logging.getLogger('mujeeb.outreach')

async def dispatch_daily_cohort(limit: int = 30, interval_seconds: int = 3):
    settings = get_settings()
    resend_api_key = settings.resend_api_key or os.getenv('RESEND_API_KEY', '')
    from_email = settings.resend_from_email or os.getenv('RESEND_FROM_EMAIL', 'contact@usemujeeb.com')
    waapi_token = settings.waapi_api_token or os.getenv('WAAPI_API_TOKEN', '')
    waapi_instance = os.getenv('WAAPI_INSTANCE_ID', '')
    
    print(f'=== LAUNCHING AUTONOMOUS OUTREACH DISPATCHER (Target: {limit} stores) ===')
    
    async with SessionLocal() as session:
        query = select(AcquisitionProspect).where(
            AcquisitionProspect.status.in_(['ready', 'new', 'qualified']),
            AcquisitionProspect.score >= 80
        ).order_by(AcquisitionProspect.score.desc()).limit(limit)
        
        prospects = list((await session.scalars(query)).all())
        print(f'Selected {len(prospects)} prospects for today.')
        
        sent_wa = 0
        sent_email = 0
        sent_ig = 0
        
        for idx, prospect in enumerate(prospects, 1):
            company_name = prospect.company.split('(')[0].strip()
            arabic_pitch = prospect.message_draft or (
                f'السلام عليكم ورحمة الله وبركاته،\n\n'
                f'معك أيوب من منصة مجيب (Mujeeb.com).\n\n'
                f'لاحظت تميز متجركم «{company_name}» وتوفيركم لخيار الدفع عند الاستلام (COD) في المملكة.\n\n'
                f'نحن نساعد المتاجر على أتمتة تأكيد الطلبات واستلام موقع العميل (GPS) فورياً عبر واتساب لتفادي المرتجعات وتوفير وقت الفريق.\n\n'
                f'يسعدنا تفعيل تجربة مجانية لكم على 50 طلباً حقيقياً:\n'
                f'https://usemujeeb.com/#book\n\n'
                f'شكراً لوقتكم.'
            )
            
            dispatched = False
            # 1. Primary: WhatsApp via WaAPI
            if waapi_token and waapi_instance and prospect.public_phone:
                clean_phone = ''.join(filter(str.isdigit, prospect.public_phone))
                try:
                    res = await send_whatsapp_via_waapi(
                        instance_id=waapi_instance,
                        api_token=waapi_token,
                        phone_number=clean_phone,
                        message=arabic_pitch
                    )
                    if res.get('status') == 'success':
                        sent_wa += 1
                        dispatched = True
                        prospect.outreach_channel = 'whatsapp_business'
                        print(f'[{idx}/{len(prospects)}] WA Sent to {prospect.company} (+{clean_phone})')
                except Exception as e:
                    print(f'[{idx}/{len(prospects)}] WA Failed for {prospect.company}: {e}')
                    
            # 2. Secondary / Fallback: B2B Email via Resend
            if not dispatched and prospect.public_email and resend_api_key:
                try:
                    await send_email_via_resend(
                        api_key=resend_api_key,
                        from_email=from_email,
                        to_email=prospect.public_email,
                        subject=f'تجربة مجانية لتأكيد طلبات الدفع عند الاستلام — متجر {company_name}',
                        body_text=arabic_pitch
                    )
                    sent_email += 1
                    dispatched = True
                    prospect.outreach_channel = 'business_email'
                    print(f'[{idx}/{len(prospects)}] Email Sent to {prospect.company} ({prospect.public_email})')
                except Exception as e:
                    print(f'[{idx}/{len(prospects)}] Email Failed for {prospect.company}: {e}')
                    
            if dispatched:
                prospect.status = 'contacted'
                prospect.last_contacted_at = datetime.now(UTC)
                prospect.contact_attempts = (prospect.contact_attempts or 0) + 1
                await session.commit()
                
            if idx < len(prospects):
                await asyncio.sleep(interval_seconds)
                
        # Send Daily Report to Owner Telegram
        summary = (
            f'🚀 <b>RAPPORT DE PROSPECTION AUTOMATISÉE ({limit}/JOUR)</b>\n'
            f'━━━━━━━━━━━━━━━━━━━━\n'
            f'📱 <b>WhatsApp (WaAPI)</b> : <b>{sent_wa}</b>\n'
            f'✉️ <b>Emails B2B (Resend)</b> : <b>{sent_email}</b>\n'
            f'🎯 <b>Total nouveaux prospects contactés</b> : <b>{sent_wa + sent_email}/{len(prospects)}</b>\n\n'
            f'⚡️ <i>Automatisation 100% opérationnelle. 0 action manuelle requise !</i>'
        )
        await send_telegram_notification(summary)
        print('\n=== OUTREACH DISPATCH SUMMARY SENT TO TELEGRAM ===')

if __name__ == '__main__':
    asyncio.run(dispatch_daily_cohort(limit=10, interval_seconds=2))

