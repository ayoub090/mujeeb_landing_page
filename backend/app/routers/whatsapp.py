
import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.config import get_settings
from app.crypto import encrypt_text
from app.database import get_session
from app.models import Store, User, WhatsAppAccount
from app.schemas import EmbeddedSignupInput
from app.services.lifecycle import record_lifecycle_event

router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])
settings = get_settings()


@router.post("/embedded-signup", status_code=201)
async def complete_embedded_signup(
    payload: EmbeddedSignupInput,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    store = await session.scalar(
        select(Store).where(Store.id == payload.store_id, Store.owner_id == user.id)
    )
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    if not settings.meta_embedded_signup_enabled:
        raise HTTPException(status_code=423, detail="Embedded Signup is awaiting Meta approval")
    if not settings.meta_app_id or not settings.meta_app_secret:
        raise HTTPException(status_code=503, detail="Meta integration is not configured")

    token_url = f"https://graph.facebook.com/{settings.meta_graph_version}/oauth/access_token"
    async with httpx.AsyncClient(timeout=15) as client:
        token_response = await client.get(
            token_url,
            params={
                "client_id": settings.meta_app_id,
                "client_secret": settings.meta_app_secret,
                "code": payload.code,
                "redirect_uri": settings.meta_embedded_signup_redirect_uri,
            },
        )
        if token_response.is_error:
            raise HTTPException(status_code=502, detail="Meta authorization failed")
        access_token = token_response.json().get("access_token")
        if not access_token:
            raise HTTPException(status_code=502, detail="Meta did not return an access token")

        phone_response = await client.get(
            f"https://graph.facebook.com/{settings.meta_graph_version}/{payload.phone_number_id}",
            params={"fields": "id,display_phone_number,verified_name", "access_token": access_token},
        )
        if phone_response.is_error:
            raise HTTPException(status_code=502, detail="Unable to verify the WhatsApp number")
        phone = phone_response.json()
        if str(phone.get("id")) != payload.phone_number_id:
            raise HTTPException(status_code=400, detail="WhatsApp phone ownership check failed")
        waba_response = await client.get(
            f"https://graph.facebook.com/{settings.meta_graph_version}/{payload.waba_id}/phone_numbers",
            params={"fields": "id", "access_token": access_token},
        )
        if waba_response.is_error or payload.phone_number_id not in {
            str(item.get("id")) for item in (waba_response.json().get("data") or [])
        }:
            raise HTTPException(status_code=400, detail="WhatsApp business account ownership check failed")

    account = await session.scalar(
        select(WhatsAppAccount).where(
            WhatsAppAccount.store_id == store.id,
            WhatsAppAccount.phone_number_id == payload.phone_number_id,
        )
    )
    if account is None:
        account = WhatsAppAccount(
            store_id=store.id,
            waba_id=payload.waba_id,
            phone_number_id=payload.phone_number_id,
            access_token_encrypted=encrypt_text(access_token),
        )
        session.add(account)
    else:
        account.waba_id = payload.waba_id
        account.access_token_encrypted = encrypt_text(access_token)
        account.status = "connected"
    if phone.get("display_phone_number"):
        account.display_phone_encrypted = encrypt_text(phone["display_phone_number"])
    await record_lifecycle_event(
        session, "whatsapp_connected", user_id=user.id, store_id=store.id
    )
    await session.commit()
    return {"status": "connected", "phone_number_id": payload.phone_number_id}
