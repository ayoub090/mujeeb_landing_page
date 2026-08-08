import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.crypto import decrypt_text
from app.models import Integration, Order, Platform


async def sync_order_to_google_sheet(order: Order, store_id: uuid.UUID, session: AsyncSession) -> None:
    # Query Google Sheets integration linked with this store
    integration = await session.scalar(
        select(Integration).where(
            Integration.store_id == store_id,
            Integration.platform == Platform.custom,
            Integration.external_store_id == "google_sheets",
            Integration.is_connected == True
        )
    )
    if not integration:
        return

    try:
        url = decrypt_text(integration.access_token_encrypted)
    except Exception:
        return

    if not url:
        return

    payload = {
        "order_id": str(order.id),
        "external_order_number": order.external_order_number or str(order.id)[:8],
        "amount": float(order.amount),
        "currency": order.currency,
        "status": order.status.value,
        "gps_lat": float(order.gps_lat) if order.gps_lat else None,
        "gps_lng": float(order.gps_lng) if order.gps_lng else None,
        "items": order.items,
        "created_at": order.created_at.isoformat()
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(url, json=payload)
    except Exception:
        # Ignore integration sheets HTTP errors so the core workflow stays unaffected
        pass
