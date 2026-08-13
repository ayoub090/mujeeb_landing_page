from __future__ import annotations

import secrets
import uuid

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, require_superadmin
from app.config import get_settings
from app.crypto import decrypt_text, encrypt_text
from app.database import get_session
from app.models import Store, User, WaapiConnection

router = APIRouter(prefix="/api/waapi", tags=["waapi"])

class ConnectInput(BaseModel):
    store_id: uuid.UUID
    instance_id: str = Field(min_length=1, max_length=64)
    api_token: str = Field(min_length=10)

class ProvisionInput(BaseModel):
    store_id: uuid.UUID


class SendTestMessageInput(BaseModel):
    store_id: uuid.UUID


def qr_image_source(payload: object) -> str | None:
    """Return a browser-safe QR source from the WAAPI response."""
    value = payload
    if isinstance(payload, dict):
        nested = payload.get("data")
        value = payload.get("base64") or payload.get("qr")
        if not value and isinstance(nested, dict):
            value = nested.get("base64") or nested.get("qr")
    if not isinstance(value, str) or not value.strip():
        return None
    value = value.strip()
    if value.startswith(("data:image/", "https://", "http://")):
        return value
    return f"data:image/png;base64,{value}"


def merchant_connection_status(connection: object | None, display_phone: str | None) -> dict[str, object]:
    """Return only merchant-facing connection information.

    Provider instance identifiers, webhook values and provider tokens remain
    server-side implementation details and must not reach the dashboard.
    """
    if connection is None:
        return {"configured": False, "connected": False}
    connected = getattr(connection, "status", None) == "ready"
    return {
        "configured": True,
        "connected": connected,
        "display_phone": display_phone if connected else None,
        "status": getattr(connection, "status", None),
    }


async def owned(store_id, user, session):
    store = await session.scalar(select(Store).where(Store.id == store_id, Store.owner_id == user.id))
    if not store: raise HTTPException(404, "Store not found")
    return store

@router.post("/connect")
async def connect(payload: ConnectInput, user: User = Depends(require_superadmin), session: AsyncSession = Depends(get_session)):
    await owned(payload.store_id, user, session)
    if "@" in payload.instance_id or not payload.instance_id.strip().isdigit():
        raise HTTPException(422, "WAAPI instance ID must be the numeric ID from your WaAPI dashboard")
    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(f"{str(settings.waapi_base_url).rstrip('/')}/instances/{payload.instance_id}", headers={"Authorization": f"Bearer {payload.api_token}", "Accept":"application/json"})
    except httpx.HTTPError as exc:
        raise HTTPException(502, "WAAPI is temporarily unreachable. Please retry.") from exc
    if response.is_error: raise HTTPException(502, "WAAPI instance could not be verified")
    webhook_token = secrets.token_urlsafe(32)
    row = await session.scalar(select(WaapiConnection).where(WaapiConnection.store_id == payload.store_id))
    if not row:
        row = WaapiConnection(store_id=payload.store_id, instance_id=payload.instance_id, api_token_encrypted=encrypt_text(payload.api_token), webhook_token_encrypted=encrypt_text(webhook_token))
        session.add(row)
    else:
        row.instance_id = payload.instance_id; row.api_token_encrypted = encrypt_text(payload.api_token); row.webhook_token_encrypted = encrypt_text(webhook_token); row.status = "configured"
    await session.commit()
    return {"status":"connected", "instance_id":payload.instance_id, "webhook_path":f"/api/waapi/webhooks/{webhook_token}"}

@router.post("/provision")
async def provision(payload: ProvisionInput, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    """Create and configure a WaAPI instance using Mujeeb's provider account.
    The merchant never sees the provider token; they only receive a QR image.
    """
    await owned(payload.store_id, user, session)
    settings = get_settings()
    if not settings.waapi_api_token:
        raise HTTPException(503, "WAAPI provisioning is not configured yet")
    headers = {"Authorization": f"Bearer {settings.waapi_api_token}", "Accept":"application/json", "Content-Type":"application/json"}
    row = await session.scalar(select(WaapiConnection).where(WaapiConnection.store_id == payload.store_id))
    webhook_token = (
        decrypt_text(row.webhook_token_encrypted)
        if row and row.webhook_token_encrypted
        else secrets.token_urlsafe(32)
    )
    webhook_url = f"{str(settings.waapi_webhook_base_url).rstrip('/')}/{webhook_token}"
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            # A store gets exactly one provider instance. Reusing it makes the
            # endpoint idempotent and prevents repeated button clicks from
            # creating billable duplicate instances.
            if row:
                existing = await client.get(
                    f"{str(settings.waapi_base_url).rstrip('/')}/instances/{row.instance_id}",
                    headers=headers,
                )
                if existing.is_success:
                    updated = await client.put(
                        f"{str(settings.waapi_base_url).rstrip('/')}/instances/{row.instance_id}",
                        headers=headers,
                        json={"webhook": {"url": webhook_url, "events": ["qr", "ready", "authenticated", "disconnected", "message", "message_create"]}},
                    )
                    if updated.is_error:
                        raise HTTPException(502, "WAAPI webhook setup failed")
                    qr = await client.get(
                        f"{str(settings.waapi_base_url).rstrip('/')}/instances/{row.instance_id}/client/qr",
                        headers=headers,
                    )
                    qr_data = qr.json() if qr.is_success else {}
                    row.api_token_encrypted = encrypt_text(settings.waapi_api_token)
                    row.status = "provisioned" if row.status != "ready" else "ready"
                    await session.commit()
                    return {"status": "qr_ready", "qr": qr_image_source(qr_data), "reused": True}
            # WAAPI creates the instance first; webhook subscription is applied
            # with the update endpoint immediately afterwards. Sending webhook
            # fields in the create request is rejected by some API versions.
            created = await client.post(
                f"{str(settings.waapi_base_url).rstrip('/')}/instances",
                headers=headers,
                json={"name": f"mujeeb-{payload.store_id}"},
            )
            if created.is_error:
                detail = created.text[:300]
                raise HTTPException(502, f"WAAPI could not create the WhatsApp instance ({created.status_code}): {detail}")
            data = created.json()
            instance = data.get("instance") if isinstance(data, dict) else None
            if not isinstance(instance, dict):
                instance = data
            instance_id = str(instance.get("id") or instance.get("instanceId") or "")
            if not instance_id.isdigit():
                raise HTTPException(502, "WAAPI returned an invalid instance ID")
            updated = await client.put(
                f"{str(settings.waapi_base_url).rstrip('/')}/instances/{instance_id}",
                headers=headers,
                json={"webhook": {"url": webhook_url, "events": ["qr", "ready", "authenticated", "disconnected", "message", "message_create"]}},
            )
            if updated.is_error:
                detail = updated.text[:300]
                raise HTTPException(502, f"WAAPI instance created but webhook setup failed ({updated.status_code}): {detail}")
            qr = await client.get(f"{str(settings.waapi_base_url).rstrip('/')}/instances/{instance_id}/client/qr", headers=headers)
            qr_data = qr.json() if qr.is_success else {}
    except httpx.HTTPError as exc:
        raise HTTPException(502, "WAAPI is temporarily unreachable") from exc
    if not row:
        row = WaapiConnection(store_id=payload.store_id, instance_id=instance_id, api_token_encrypted=encrypt_text(settings.waapi_api_token), webhook_token_encrypted=encrypt_text(webhook_token), status="provisioned")
        session.add(row)
    else:
        row.instance_id = instance_id; row.api_token_encrypted = encrypt_text(settings.waapi_api_token); row.webhook_token_encrypted = encrypt_text(webhook_token); row.status = "provisioned"
    await session.commit()
    return {"status":"qr_ready", "qr":qr_image_source(qr_data)}

@router.get("/status")
async def status(store_id: uuid.UUID, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    await owned(store_id, user, session)
    row = await session.scalar(select(WaapiConnection).where(WaapiConnection.store_id == store_id))
    return merchant_connection_status(
        row,
        decrypt_text(user.phone_encrypted) if row and row.status == "ready" and user.phone_encrypted else None,
    )


@router.post("/test-message")
async def send_test_message(
    payload: SendTestMessageInput,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Send the merchant's own phone a real connection test, without exposing provider data."""
    await owned(payload.store_id, user, session)
    row = await session.scalar(select(WaapiConnection).where(WaapiConnection.store_id == payload.store_id))
    if not row or row.status != "ready":
        raise HTTPException(409, "WhatsApp is not connected yet")
    if not user.phone_encrypted:
        raise HTTPException(422, "A merchant phone number is required for the test")
    from app.crypto import decrypt_text

    phone = decrypt_text(user.phone_encrypted)
    chat_id = f"{''.join(character for character in phone if character.isdigit())}@c.us"
    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{str(settings.waapi_base_url).rstrip('/')}/instances/{row.instance_id}/client/action/send-message",
                headers={
                    "Authorization": f"Bearer {decrypt_text(row.api_token_encrypted)}",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                json={
                    "chatId": chat_id,
                    "message": "مجيب جاهز. هذه رسالة اختبار للتأكد من ربط متجرك وواتساب بنجاح.",
                },
            )
    except httpx.HTTPError as exc:
        raise HTTPException(502, "WhatsApp is temporarily unreachable") from exc
    if response.is_error:
        raise HTTPException(502, "Unable to send the test message")
    return {"status": "sent"}

@router.post("/webhooks/{token}", status_code=202)
async def webhook(token: str, request: Request, session: AsyncSession = Depends(get_session)):
    raw = await request.json()
    rows = await session.scalars(select(WaapiConnection))
    match = None
    from app.crypto import decrypt_text
    for row in rows:
        if row.webhook_token_encrypted and secrets.compare_digest(decrypt_text(row.webhook_token_encrypted), token): match = row; break
    if not match: raise HTTPException(401, "Invalid webhook token")
    event = raw.get("event")
    if event in {"authenticated", "ready"}:
        match.status = "ready"
        await session.commit()
    elif event in {"auth_failure", "disconnected"}:
        match.status = "disconnected"
        await session.commit()
    # The provider only needs an acknowledgement. Never echo its internal
    # instance identifier back over a public webhook endpoint.
    return {"received": True, "store_id": str(match.store_id), "event": event}
