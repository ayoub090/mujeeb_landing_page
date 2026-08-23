import asyncio
import logging
import os
from typing import Any

from sqlalchemy import select
from app.config import get_settings
from app.database import SessionLocal
from app.models import AcquisitionProspect
from app.services.telegram import send_telegram_notification

logger = logging.getLogger("mujeeb.instagram_cohort")

async def generate_daily_instagram_cohort(limit: int = 30):
    print(f'=== GENERATING DAILY MANUAL INSTAGRAM OUTREACH COHORT (Target: {limit}) ===')
    
    async with SessionLocal() as session:
        query = select(AcquisitionProspect).where(
            AcquisitionProspect.score >= 75
        ).order_by(AcquisitionProspect.score.desc()).limit(limit)
        
        prospects = list((await session.scalars(query)).all())
        print(f'Found {len(prospects)} prospects for Instagram cohort.')
        
        # Send Header to Telegram
        header = (
            f'📸 <b>COHORTE D\'OUTREACH INSTAGRAM DU JOUR ({len(prospects)} BOUTIQUES)</b>\n'
            f'━━━━━━━━━━━━━━━━━━━━\n'
            f'Voici votre liste de <b>{len(prospects)} messages Instagram personnalisés</b>.\n'
            f'💡 <i>Chaque fiche contient le lien direct vers le profil et le texte prêt à copier/coller.</i>'
        )
        await send_telegram_notification(header)
        await asyncio.sleep(0.5)
        
        for idx, p in enumerate(prospects, 1):
            company_name = p.company.split('(')[0].strip()
            
            # Extract clean domain name for fallback IG search
            domain_handle = p.canonical_website.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0].split('.')[0]
            ig_url = f'https://instagram.com/{domain_handle}'
            
            ig_pitch = (
                f'مرحباً أخي العزيز، تحياتي لفريق متجر {company_name} 🌸\n\n'
                f'شفت متجركم الجميل على سلة، ونظام الدفع عند الاستلام عندكم.\n\n'
                f'نحن في منصة «مجيب» نساعدكم تأكدوا طلبيات الـ COD وتستلموا اللوكيشن الجغرافي للعميل تلقائياً عبر الواتساب في ثوانٍ قبل ما يطلع المندوب (يقلل المرتجعات للصفر تقريباً).\n\n'
                f'حابين نفعّل لكم 50 تأكيد مجاني لتجربة النظام؟\n'
                f'الفيديو والتفاصيل هنا: usemujeeb.com/#book'
            )
            
            card = (
                f'📸 <b>PROSPECT INSTAGRAM #{idx}/{len(prospects)}</b>\n'
                f'🏬 <b>Boutique</b> : {p.company}\n'
                f'🌐 <b>Site</b> : {p.canonical_website}\n'
                f'📊 <b>Score ICP</b> : <b>{p.score}/100</b>\n\n'
                f'💬 <b>Message DM à copier :</b>\n'
                f'<blockquote>{ig_pitch}</blockquote>\n\n'
                f'👉 <a href=\"{ig_url}\"><b>[📸 CLIQUER POUR OUVRIR LE PROFIL INSTAGRAM]</b></a>'
            )
            
            await send_telegram_notification(card)
            await asyncio.sleep(0.4)
            
        print('\n=== ALL INSTAGRAM PROSPECT CARDS DISPATCHED TO TELEGRAM! ===')

if __name__ == '__main__':
    asyncio.run(generate_daily_instagram_cohort(limit=10))
