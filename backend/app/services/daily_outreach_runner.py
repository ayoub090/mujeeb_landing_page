import asyncio
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

backend_dir = Path(r'C:\Users\DELL\Desktop\mujeeb_landing_page\backend')
sys.path.insert(0, str(backend_dir))
sys.stdout.reconfigure(encoding='utf-8')

os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///' + str(backend_dir / 'mujeeb.sqlite3')
os.environ['TELEGRAM_BOT_TOKEN'] = '7989031523:AAG06PB2n4nrYkkThYXwczdpngMzL9RabqA'
os.environ['TELEGRAM_CHAT_ID'] = '5547351734'

from sqlalchemy import select
from app.database import SessionLocal
from app.models import AcquisitionProspect
from app.services.telegram import send_telegram_notification
from app.services.automated_outreach import send_whatsapp_via_waapi

WAAPI_INSTANCE_ID = os.getenv('WAAPI_INSTANCE_ID', '102227')
WAAPI_API_TOKEN = os.getenv('WAAPI_API_TOKEN', '')

async def run_daily_outreach(batch_size: int = 5, delay_seconds: int = 5):
    print(f'=== STARTING AUTOMATED OUTREACH BATCH (Limit: {batch_size}) ===')
    
    results = []
    async with SessionLocal() as session:
        query = select(AcquisitionProspect).where(
            AcquisitionProspect.status.in_(['ready', 'new', 'qualified']),
            AcquisitionProspect.score >= 80,
            AcquisitionProspect.public_phone.is_not(None)
        ).order_by(AcquisitionProspect.score.desc()).limit(batch_size)
        
        prospects = list((await session.scalars(query)).all())
        print(f'Found {len(prospects)} high-priority prospects to contact automatically.')
        
        if not prospects:
            print('No prospects in queue.')
            return

        for idx, prospect in enumerate(prospects, 1):
            print(f'\n[{idx}/{len(prospects)}] Processing {prospect.company} ({prospect.canonical_website})...')
            
            msg = prospect.message_draft
            if not msg:
                company_name = prospect.company.split('(')[0].strip()
                msg = (
                    f'السلام عليكم ورحمة الله وبركاته،\n\n'
                    f'معك أيوب من منصة مجيب (Mujeeb.com).\n\n'
                    f'لاحظت تميز متجركم «{company_name}» وحرصكم على توفير خيار الدفع عند الاستلام (COD) لعملائكم في المملكة.\n\n'
                    f'نحن نساعد المتاجر على سلة وزد في أتمتة تأكيد طلبات الدفع عند الاستلام عبر واتساب واستلام اللوكيشن تلقائياً قبل الشحن لتقليل المرتجعات وتوفير وقت فريقكم.\n\n'
                    f'يسعدنا تفعيل تجربة مجانية لمتجركم على 50 طلباً حقيقياً لمقارنة النتائج دون أي تغيير في شركة الشحن المعتمدة لديكم:\n'
                    f'https://usemujeeb.com/#book\n\n'
                    f'شكراً لوقتكم، وإذا كان التوقيت غير مناسب يسعدني إعلامي وسأتوقف عن المتابعة.'
                )
                prospect.message_draft = msg

            phone = prospect.public_phone
            clean_phone = ''.join(filter(str.isdigit, phone))
            
            try:
                print(f'-> Sending automated WhatsApp to +{clean_phone} via WaAPI Instance #{WAAPI_INSTANCE_ID}...')
                resp = await send_whatsapp_via_waapi(
                    instance_id=WAAPI_INSTANCE_ID,
                    api_token=WAAPI_API_TOKEN,
                    phone_number=clean_phone,
                    message=msg
                )
                status_text = resp.get('status')
                print(f'-> Success! WaAPI Response: {status_text}')
                
                prospect.status = 'contacted'
                prospect.outreach_channel = 'whatsapp_business'
                prospect.last_contacted_at = datetime.now(UTC)
                prospect.contact_attempts = (prospect.contact_attempts or 0) + 1
                await session.commit()
                
                results.append({
                    'company': prospect.company,
                    'phone': clean_phone,
                    'status': 'SENT',
                    'url': prospect.canonical_website
                })
            except Exception as e:
                print(f'-> Failed to send to {prospect.company}: {e}')
                results.append({
                    'company': prospect.company,
                    'phone': clean_phone,
                    'status': f'FAILED: {e}',
                    'url': prospect.canonical_website
                })
            
            if idx < len(prospects):
                print(f'Waiting {delay_seconds}s before next send for natural spacing...')
                await asyncio.sleep(delay_seconds)
                
    success_count = sum(1 for r in results if r['status'] == 'SENT')
    summary_msg = (
        f'🤖 <b>RAPPORT D\'OUTREACH AUTOMATIQUE WAAPI</b>\n'
        f'━━━━━━━━━━━━━━━━━━━━\n'
        f'✅ <b>Messages envoyés avec succès</b> : <b>{success_count}/{len(results)}</b>\n'
        f'📱 <b>Numéro émetteur</b> : <code>+212 723-193155</code> (WaAPI #102227)\n\n'
        f'📋 <b>Détail des prospects contactés :</b>\n'
    )
    for r in results:
        icon = '✅' if r['status'] == 'SENT' else '❌'
        comp = r['company']
        ph = r['phone']
        st = r['status']
        summary_msg += f'{icon} <b>{comp}</b> (+{ph}) — <i>{st}</i>\n'
        
    summary_msg += (
        '\n⚡️ <i>Le système surveille les réponses en temps réel. Vous serez notifié dès qu\'un prospect répond !</i>'
    )
    
    await send_telegram_notification(summary_msg)
    print('\n=== SUMMARY DISPATCHED TO TELEGRAM SUCCESSFULLY ===')

if __name__ == '__main__':
    asyncio.run(run_daily_outreach(batch_size=5, delay_seconds=6))
