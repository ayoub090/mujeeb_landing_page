import asyncio
import smtplib
from email.message import EmailMessage
from html import escape

import httpx

from app.config import get_settings


def render_email(kind: str, payload: dict) -> tuple[str, str, str]:
    name = escape(str(payload.get("name") or "صاحب المتجر"))
    store = escape(str(payload.get("store") or "متجرك"))
    remaining = int(payload.get("remaining") or 0)
    templates = {
        "welcome": (
            "مرحباً بك في تجربة مجيب",
            f"أهلاً {name}، بدأت تجربة {store}. اربط متجرك وأرسل أول طلب دفع عند الاستلام.",
            f"<p>أهلاً {name}،</p><p>بدأت تجربة <strong>{store}</strong>. اربط متجرك وأرسل أول طلب دفع عند الاستلام لتظهر لك درجة المخاطر وحالة التأكيد.</p>",
        ),
        "pilot_40": (
            "تقرير مجيب يقترب — بقي 10 طلبات",
            f"حلّل مجيب 40 طلباً لـ{store}. بقي {remaining or 10} طلبات قبل تقرير التجربة.",
            f"<p>حلّل مجيب 40 طلباً لـ<strong>{store}</strong>.</p><p>بقي <strong>{remaining or 10}</strong> طلبات قبل تقرير التجربة ومقارنة النتائج بخط الأساس.</p>",
        ),
        "deletion_scheduled": (
            "تمت جدولة حذف حساب مجيب",
            "تمت جدولة حذف الحساب والبيانات المرتبطة. يمكنك إلغاء الطلب من لوحة الحساب قبل موعد التنفيذ.",
            "<p>تمت جدولة حذف حسابك والبيانات المرتبطة به.</p><p>يمكنك إلغاء الطلب من لوحة الحساب قبل موعد التنفيذ الموضح هناك.</p>",
        ),
    }
    return templates.get(
        kind,
        ("إشعار من مجيب", "لديك إشعار جديد من مجيب.", "<p>لديك إشعار جديد من مجيب.</p>"),
    )


def _html_document(content: str) -> str:
    return (
        "<!doctype html><html lang='ar' dir='rtl'><body style='font-family:Arial;"
        "line-height:1.8;color:#172033;max-width:620px;margin:auto;padding:24px'>"
        f"{content}<p><a href='https://app.usemujeeb.com'>فتح لوحة مجيب</a></p>"
        "<hr><small>رسالة تشغيلية مرتبطة بحسابك في مجيب، الذي يديره Ayoub Fadil.</small>"
        "</body></html>"
    )


async def _send_with_resend(recipient: str, subject: str, plain: str, html: str) -> None:
    settings = get_settings()
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            f"{settings.resend_api_base.rstrip('/')}/emails",
            headers={"Authorization": f"Bearer {settings.resend_api_key}"},
            json={
                "from": f"{settings.resend_from_name} <{settings.resend_from_email}>",
                "to": [recipient],
                "subject": subject,
                "text": plain,
                "html": html,
            },
        )
        response.raise_for_status()


async def send_email(recipient: str, kind: str, payload: dict) -> None:
    settings = get_settings()
    subject, plain, content = render_email(kind, payload)
    html = _html_document(content)

    if settings.resend_api_key and settings.resend_from_email:
        await _send_with_resend(recipient, subject, plain, html)
        return
    if not settings.smtp_host or not settings.smtp_from_email:
        raise RuntimeError("Email provider is not configured")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
    message["To"] = recipient
    message.set_content(plain)
    message.add_alternative(html, subtype="html")

    def deliver() -> None:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as client:
            if settings.smtp_use_tls:
                client.starttls()
            if settings.smtp_username:
                client.login(settings.smtp_username, settings.smtp_password)
            client.send_message(message)

    await asyncio.to_thread(deliver)
