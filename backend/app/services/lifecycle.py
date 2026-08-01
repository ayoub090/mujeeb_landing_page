import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crypto import encrypt_text, stable_hash
from app.models import EmailJob, FunnelEvent


async def record_lifecycle_event(
    session: AsyncSession,
    event_name: str,
    *,
    user_id: uuid.UUID | None = None,
    store_id: uuid.UUID | None = None,
    properties: dict | None = None,
) -> None:
    session.add(
        FunnelEvent(
            event_name=event_name,
            session_id=f"server-{uuid.uuid4().hex}",
            path="/server/lifecycle",
            user_id=user_id,
            store_id=store_id,
            source="server",
            properties=properties or {},
        )
    )


async def enqueue_email(
    session: AsyncSession,
    *,
    dedupe_key: str,
    kind: str,
    recipient: str,
    payload: dict | None = None,
) -> bool:
    if await session.scalar(select(EmailJob.id).where(EmailJob.dedupe_key == dedupe_key)):
        return False
    session.add(
        EmailJob(
            dedupe_key=dedupe_key,
            kind=kind,
            recipient_encrypted=encrypt_text(recipient.lower()),
            recipient_hash=stable_hash(recipient),
            payload=payload or {},
            next_attempt_at=datetime.now(UTC),
        )
    )
    return True
