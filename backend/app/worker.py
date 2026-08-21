import asyncio
import logging
import smtplib
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select

from app.crypto import decrypt_text
from app.database import SessionLocal
from app.models import BusinessLead, DataDeletionRequest, EmailJob, User
from app.services.email_service import send_email

logger = logging.getLogger("mujeeb.worker")


async def process_email_jobs() -> None:
    async with SessionLocal() as session:
        jobs = list((await session.scalars(
            select(EmailJob)
            .where(EmailJob.status == "queued", EmailJob.next_attempt_at <= datetime.now(UTC))
            .order_by(EmailJob.created_at)
            .limit(20)
            .with_for_update(skip_locked=True)
        )).all())
        for job in jobs:
            job.status = "processing"
            await session.flush()
            try:
                await send_email(decrypt_text(job.recipient_encrypted), job.kind, job.payload)
            except RuntimeError as exc:
                if str(exc) == "Email provider is not configured":
                    job.status = "queued"
                    job.last_error = str(exc)
                    job.next_attempt_at = datetime.now(UTC) + timedelta(hours=1)
                    continue
                job.attempts += 1
                job.last_error = str(exc)[:1000]
                job.status = "failed" if job.attempts >= 8 else "queued"
                if job.status == "queued":
                    job.next_attempt_at = datetime.now(UTC) + timedelta(minutes=2 ** job.attempts)
            except (OSError, ValueError, smtplib.SMTPException) as exc:
                job.attempts += 1
                job.last_error = str(exc)[:1000]
                if job.attempts >= 8:
                    job.status = "failed"
                else:
                    job.status = "queued"
                    job.next_attempt_at = datetime.now(UTC) + timedelta(minutes=2 ** job.attempts)
            else:
                job.status = "sent"
                job.sent_at = datetime.now(UTC)
        await session.commit()


async def process_deletions() -> None:
    async with SessionLocal() as session:
        requests = list((await session.scalars(
            select(DataDeletionRequest)
            .where(
                DataDeletionRequest.status == "scheduled",
                DataDeletionRequest.scheduled_for <= datetime.now(UTC),
            )
            .limit(10)
            .with_for_update(skip_locked=True)
        )).all())
        for request in requests:
            request.status = "processing"
            await session.flush()
            user = await session.get(User, request.user_id) if request.user_id else None
            if user:
                await session.delete(user)
                await session.flush()
            await session.execute(delete(EmailJob).where(EmailJob.recipient_hash == request.email_hash))
            await session.execute(delete(BusinessLead).where(BusinessLead.email_hash == request.email_hash))
            request.status = "completed"
            request.completed_at = datetime.now(UTC)
        await session.commit()


async def run() -> None:
    while True:
        try:
            await process_email_jobs()
            await process_deletions()
        except Exception:
            # Keep the worker alive; individual errors are recorded on each job when possible.
            logger.exception("Lifecycle worker iteration failed")
        await asyncio.sleep(20)


if __name__ == "__main__":
    asyncio.run(run())
