import secrets
import uuid
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends, HTTPException, Request, Response, status
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_session
from app.models import User

password_hash = PasswordHash.recommended()
settings = get_settings()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def create_token(user_id: uuid.UUID, kind: str, lifetime: timedelta) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {"sub": str(user_id), "type": kind, "iat": now, "exp": now + lifetime, "jti": secrets.token_urlsafe(16)},
        settings.jwt_secret,
        algorithm="HS256",
    )


def set_auth_cookies(response: Response, user_id: uuid.UUID) -> None:
    common = {
        "httponly": True,
        "secure": settings.secure_cookies,
        "samesite": "lax",
        "domain": settings.cookie_domain,
        "path": "/",
    }
    response.set_cookie(
        "mujeeb_access",
        create_token(user_id, "access", timedelta(minutes=settings.access_token_minutes)),
        max_age=settings.access_token_minutes * 60,
        **common,
    )
    response.set_cookie(
        "mujeeb_refresh",
        create_token(user_id, "refresh", timedelta(days=settings.refresh_token_days)),
        max_age=settings.refresh_token_days * 86400,
        **common,
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie("mujeeb_access", domain=settings.cookie_domain, path="/")
    response.delete_cookie("mujeeb_refresh", domain=settings.cookie_domain, path="/")


def decode_token(token: str, expected_type: str) -> uuid.UUID:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        if payload.get("type") != expected_type:
            raise ValueError("wrong token type")
        return uuid.UUID(payload["sub"])
    except (jwt.PyJWTError, ValueError, KeyError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session invalide") from exc


async def get_current_user(
    request: Request, session: AsyncSession = Depends(get_session)
) -> User:
    token = request.cookies.get("mujeeb_access")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentification requise")
    user_id = decode_token(token, "access")
    user = await session.scalar(select(User).where(User.id == user_id, User.is_active.is_(True)))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Compte introuvable")
    return user


def is_internal_admin(user: User) -> bool:
    configured_email = get_settings().internal_admin_email.strip().lower()
    return bool(configured_email) and user.email.lower() == configured_email


def require_internal_admin(user: User) -> User:
    if not is_internal_admin(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Internal tools are not available for this account")
    return user


async def require_superadmin(user: User = Depends(get_current_user)) -> User:
    """Dependency boundary for every internal-only HTTP route.

    The dashboard may hide `/admin`, but the API remains authoritative: an
    authenticated merchant can never reach simulation, provider-instance or
    raw diagnostic endpoints unless their email matches INTERNAL_ADMIN_EMAIL.
    """
    return require_internal_admin(user)

