
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import (
    clear_auth_cookies,
    decode_token,
    get_current_user,
    hash_password,
    set_auth_cookies,
    verify_password,
)
from app.config import get_settings
from app.crypto import encrypt_text
from app.database import get_session
from app.models import Store, Subscription, User
from app.schemas import LoginInput, RegisterInput, UserOut
from app.services.capi import send_capi_event
from app.services.geoip import verify_signup_ip
from app.services.lifecycle import enqueue_email, record_lifecycle_event

router = APIRouter(prefix="/api/auth", tags=["auth"])


def source_ip(request: Request) -> str:
    settings = get_settings()
    if settings.trust_proxy_headers:
        forwarded = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        if forwarded:
            return forwarded
    return request.client.host if request.client else "127.0.0.1"


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterInput,
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    await verify_signup_ip(source_ip(request))
    email = payload.email.lower()
    if await session.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Un compte existe déjà avec cet email")

    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name.strip(),
        phone_encrypted=encrypt_text(payload.phone.strip()),
    )
    store = Store(
        name=payload.store_name.strip(),
        platform=payload.platform,
        country_code=payload.country_code,
        currency={"SA": "SAR", "AE": "AED", "KW": "KWD", "BH": "BHD", "QA": "QAR", "OM": "OMR"}[payload.country_code],
    )
    store.subscription = Subscription(plan="free", status="active")
    user.stores.append(store)
    session.add(user)
    await session.flush()
    await record_lifecycle_event(
        session,
        "signup_completed",
        user_id=user.id,
        store_id=store.id,
        properties={"platform": payload.platform.value, "country": payload.country_code},
    )
    await enqueue_email(
        session,
        dedupe_key=f"welcome:{user.id}",
        kind="welcome",
        recipient=email,
        payload={"name": user.full_name, "store": store.name},
    )
    await session.commit()
    await session.refresh(user, attribute_names=["stores"])
    background_tasks.add_task(
        send_capi_event,
        "CompleteRegistration",
        f"signup-{user.id}",
        email=user.email,
        phone=payload.phone,
        client_ip=source_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    set_auth_cookies(response, user.id)
    return user


@router.post("/login", response_model=UserOut)
async def login(
    payload: LoginInput,
    response: Response,
    session: AsyncSession = Depends(get_session),
):
    user = await session.scalar(
        select(User).options(selectinload(User.stores)).where(User.email == payload.email.lower())
    )
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email ou mot de passe invalide")
    set_auth_cookies(response, user.id)
    return user


@router.post("/refresh", status_code=204)
async def refresh(request: Request, response: Response):
    token = request.cookies.get("mujeeb_refresh")
    if not token:
        raise HTTPException(status_code=401, detail="Refresh token missing")
    user_id = decode_token(token, "refresh")
    set_auth_cookies(response, user_id)


@router.post("/logout", status_code=204)
async def logout(response: Response):
    clear_auth_cookies(response)


@router.get("/me", response_model=UserOut)
async def me(
    user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)
):
    hydrated = await session.scalar(
        select(User).options(selectinload(User.stores)).where(User.id == user.id)
    )
    return hydrated
