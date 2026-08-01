import hashlib
import hmac
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.config import get_settings
from app.crypto import encrypt_text
from app.database import get_session
from app.models import Integration, OAuthState, Platform, Store, User
from app.schemas import OAuthStartInput, ShopifyStartInput, UrlOut
from app.services.lifecycle import record_lifecycle_event

router = APIRouter(prefix="/api/integrations", tags=["integrations"])
settings = get_settings()


async def ensure_owned_store(store_id: uuid.UUID, user_id: uuid.UUID, session: AsyncSession) -> Store:
    store = await session.scalar(select(Store).where(Store.id == store_id, Store.owner_id == user_id))
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    return store


async def make_state(provider: str, store_id: uuid.UUID, session: AsyncSession) -> str:
    state = secrets.token_urlsafe(32)
    session.add(
        OAuthState(
            provider=provider,
            store_id=store_id,
            state_hash=hashlib.sha256(state.encode()).hexdigest(),
            expires_at=datetime.now(UTC) + timedelta(minutes=10),
        )
    )
    await session.commit()
    return state


async def consume_state(provider: str, state: str, session: AsyncSession) -> OAuthState:
    now = datetime.now(UTC)
    row = await session.scalar(
        select(OAuthState).where(
            OAuthState.provider == provider,
            OAuthState.state_hash == hashlib.sha256(state.encode()).hexdigest(),
            OAuthState.consumed_at.is_(None),
            OAuthState.expires_at > now,
        )
    )
    if not row:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
    row.consumed_at = now
    await session.flush()
    return row


@router.post("/salla/start", response_model=UrlOut)
async def start_salla(
    payload: OAuthStartInput,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await ensure_owned_store(payload.store_id, user.id, session)
    if not settings.salla_client_id:
        raise HTTPException(status_code=503, detail="Salla integration is not configured")
    state = await make_state("salla", payload.store_id, session)
    params = {
        "client_id": settings.salla_client_id,
        "redirect_uri": settings.salla_redirect_uri,
        "response_type": "code",
        "scope": "offline_access read_orders write_orders read_customers webhooks.read_write",
        "state": state,
    }
    return UrlOut(url=f"https://accounts.salla.sa/oauth2/auth?{urlencode(params)}")


@router.get("/salla/callback")
async def salla_callback(
    code: str = Query(...),
    state: str = Query(...),
    session: AsyncSession = Depends(get_session),
):
    state_row = await consume_state("salla", state, session)
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            "https://accounts.salla.sa/oauth2/token",
            data={
                "client_id": settings.salla_client_id,
                "client_secret": settings.salla_client_secret,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.salla_redirect_uri,
            },
        )
        response.raise_for_status()
    token = response.json()
    await register_salla_webhooks(token["access_token"])
    external_store_id = None
    async with httpx.AsyncClient(timeout=10) as client:
        info_response = await client.get(
            "https://accounts.salla.sa/oauth2/user/info",
            headers={"Authorization": f"Bearer {token['access_token']}"},
        )
        if not info_response.is_error:
            info = info_response.json()
            info_data = info.get("data") or {}
            merchant = info_data.get("merchant") or info.get("merchant") or {}
            external_store_id = str(
                info.get("id") or info_data.get("id") or merchant.get("id") or ""
            ) or None
    await upsert_integration(
        state_row.store_id, Platform.salla, token, session, external_store_id=external_store_id
    )
    await record_lifecycle_event(
        session, "store_connected", store_id=state_row.store_id, properties={"platform": "salla"}
    )
    await session.commit()
    return RedirectResponse(f"{settings.frontend_origin}/dashboard/integrations?connected=salla")


@router.post("/zid/start", response_model=UrlOut)
async def start_zid(
    payload: OAuthStartInput,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await ensure_owned_store(payload.store_id, user.id, session)
    if not settings.zid_client_id:
        raise HTTPException(status_code=503, detail="Zid integration is not configured")
    state = await make_state("zid", payload.store_id, session)
    params = {
        "client_id": settings.zid_client_id,
        "redirect_uri": settings.zid_redirect_uri,
        "response_type": "code",
        "state": state,
    }
    return UrlOut(url=f"https://oauth.zid.sa/oauth/authorize?{urlencode(params)}")


@router.get("/zid/callback")
async def zid_callback(
    code: str = Query(...),
    state: str = Query(...),
    session: AsyncSession = Depends(get_session),
):
    state_row = await consume_state("zid", state, session)
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            "https://oauth.zid.sa/oauth/token",
            data={
                "client_id": settings.zid_client_id,
                "client_secret": settings.zid_client_secret,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.zid_redirect_uri,
            },
        )
        response.raise_for_status()
    token = response.json()
    await register_zid_webhooks(token)
    zid_headers = {
        "Authorization": token.get("authorization") or token.get("Authorization", ""),
        "X-Manager-Token": token["access_token"],
        "Accept-Language": "en",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        store_response = await client.get(
            "https://api.zid.sa/v1/managers/account/store", headers=zid_headers
        )
    zid_store = (store_response.json().get("store") or {}) if not store_response.is_error else {}
    zid_store_id = zid_store.get("uuid") or zid_store.get("id")
    await upsert_integration(
        state_row.store_id, Platform.zid, token, session,
        external_store_id=str(zid_store_id) if zid_store_id else None,
    )
    await record_lifecycle_event(
        session, "store_connected", store_id=state_row.store_id, properties={"platform": "zid"}
    )
    await session.commit()
    return RedirectResponse(f"{settings.frontend_origin}/dashboard/integrations?connected=zid")


@router.post("/shopify/start", response_model=UrlOut)
async def start_shopify(
    payload: ShopifyStartInput,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await ensure_owned_store(payload.store_id, user.id, session)
    if not settings.shopify_client_id or not settings.shopify_client_secret:
        raise HTTPException(status_code=503, detail="Shopify integration is not configured")
    state = await make_state("shopify", payload.store_id, session)
    params = {
        "client_id": settings.shopify_client_id,
        "scope": settings.shopify_scopes,
        "redirect_uri": settings.shopify_redirect_uri,
        "state": state,
    }
    return UrlOut(url=f"https://{payload.shop}/admin/oauth/authorize?{urlencode(params)}")


def verify_shopify_callback(params: dict[str, str]) -> bool:
    supplied = params.get("hmac", "")
    message = "&".join(f"{key}={value}" for key, value in sorted(params.items()) if key != "hmac")
    expected = hmac.new(
        settings.shopify_client_secret.encode(), message.encode(), hashlib.sha256
    ).hexdigest()
    return bool(supplied) and hmac.compare_digest(expected, supplied)


@router.get("/shopify/callback")
async def shopify_callback(
    code: str = Query(...),
    state: str = Query(...),
    shop: str = Query(...),
    hmac_value: str = Query(..., alias="hmac"),
    timestamp: str = Query(...),
    host: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
):
    params = {"code": code, "state": state, "shop": shop, "hmac": hmac_value, "timestamp": timestamp}
    if host:
        params["host"] = host
    normalized_shop = ShopifyStartInput(store_id=uuid.uuid4(), shop=shop).shop
    if not verify_shopify_callback(params):
        raise HTTPException(status_code=401, detail="Invalid Shopify callback signature")
    state_row = await consume_state("shopify", state, session)
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            f"https://{normalized_shop}/admin/oauth/access_token",
            json={
                "client_id": settings.shopify_client_id,
                "client_secret": settings.shopify_client_secret,
                "code": code,
            },
        )
        response.raise_for_status()
    token = response.json()
    await register_shopify_webhooks(normalized_shop, token["access_token"])
    await upsert_integration(
        state_row.store_id,
        Platform.shopify,
        token,
        session,
        external_store_id=normalized_shop,
    )
    await record_lifecycle_event(
        session, "store_connected", store_id=state_row.store_id, properties={"platform": "shopify"}
    )
    await session.commit()
    return RedirectResponse(f"{settings.frontend_origin}/dashboard/integrations?connected=shopify")


async def register_shopify_webhooks(shop: str, access_token: str) -> None:
    endpoint = f"https://{shop}/admin/api/{settings.shopify_api_version}/graphql.json"
    mutation = """
      mutation CreateWebhook($topic: WebhookSubscriptionTopic!, $uri: URL!) {
        webhookSubscriptionCreate(topic: $topic, webhookSubscription: {uri: $uri, format: JSON}) {
          userErrors { field message }
        }
      }
    """
    headers = {"X-Shopify-Access-Token": access_token, "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=15) as client:
        for topic in ("ORDERS_CREATE", "APP_UNINSTALLED"):
            response = await client.post(
                endpoint,
                headers=headers,
                json={
                    "query": mutation,
                    "variables": {
                        "topic": topic,
                        "uri": f"{str(settings.app_base_url).rstrip('/')}/api/webhooks/shopify",
                    },
                },
            )
            response.raise_for_status()
            errors = ((response.json().get("data") or {}).get("webhookSubscriptionCreate") or {}).get("userErrors") or []
            if errors and not all("taken" in str(error.get("message", "")).lower() for error in errors):
                raise HTTPException(status_code=502, detail="Shopify webhook registration failed")


async def register_zid_webhooks(token: dict) -> None:
    if not settings.zid_webhook_secret:
        raise HTTPException(status_code=503, detail="Zid webhook secret is not configured")
    headers = {
        "Authorization": token.get("authorization") or token.get("Authorization", ""),
        "X-Manager-Token": token["access_token"],
        "Accept-Language": "en",
        "Content-Type": "application/json",
    }
    target = f"{str(settings.app_base_url).rstrip('/')}/api/webhooks/zid"
    async with httpx.AsyncClient(timeout=15) as client:
        for event in ("order.create", "order.status.update"):
            response = await client.post(
                "https://api.zid.sa/v1/managers/webhooks",
                headers=headers,
                json={
                    "event": event,
                    "target_url": target,
                    "conditions": {},
                    "username": "mujeeb",
                    "password": settings.zid_webhook_secret,
                },
            )
            response.raise_for_status()


async def register_salla_webhooks(access_token: str) -> None:
    if not settings.salla_webhook_secret:
        raise HTTPException(status_code=503, detail="Salla webhook secret is not configured")
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    target = f"{str(settings.app_base_url).rstrip('/')}/api/webhooks/salla"
    async with httpx.AsyncClient(timeout=15) as client:
        for event in ("order.created", "order.status.updated"):
            response = await client.post(
                "https://api.salla.dev/admin/v2/webhooks/subscribe",
                headers=headers,
                json={
                    "name": f"Mujeeb {event}",
                    "event": event,
                    "url": target,
                    "version": 2,
                    "secret": settings.salla_webhook_secret,
                },
            )
            response.raise_for_status()


@router.get("/status")
async def integration_status(
    store_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await ensure_owned_store(store_id, user.id, session)
    connected = set((await session.scalars(
        select(Integration.platform).where(
            Integration.store_id == store_id, Integration.is_connected.is_(True)
        )
    )).all())
    return {
        "salla": {"configured": bool(settings.salla_client_id and settings.salla_client_secret and settings.salla_webhook_secret), "connected": Platform.salla in connected},
        "zid": {"configured": bool(settings.zid_client_id and settings.zid_client_secret and settings.zid_webhook_secret), "connected": Platform.zid in connected},
        "shopify": {"configured": bool(settings.shopify_client_id and settings.shopify_client_secret), "connected": Platform.shopify in connected},
        "whatsapp": {"enabled": settings.meta_embedded_signup_enabled, "configured": bool(settings.meta_app_id and settings.meta_config_id)},
    }


async def upsert_integration(
    store_id: uuid.UUID,
    platform: Platform,
    token: dict,
    session: AsyncSession,
    external_store_id: str | None = None,
) -> None:
    existing = await session.scalar(
        select(Integration).where(Integration.store_id == store_id, Integration.platform == platform)
    )
    expires_at = None
    if token.get("expires_in"):
        expires_at = datetime.now(UTC) + timedelta(seconds=int(token["expires_in"]))
    values = {
        "access_token_encrypted": encrypt_text(token["access_token"]),
        "refresh_token_encrypted": encrypt_text(token["refresh_token"]) if token.get("refresh_token") else None,
        "auxiliary_token_encrypted": encrypt_text(token.get("authorization") or token.get("Authorization")) if (token.get("authorization") or token.get("Authorization")) else None,
        "expires_at": expires_at,
        "is_connected": True,
        "external_store_id": external_store_id,
    }
    if existing:
        for key, value in values.items():
            setattr(existing, key, value)
    else:
        session.add(Integration(store_id=store_id, platform=platform, **values))
