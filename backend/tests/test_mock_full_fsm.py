import base64
import os

import httpx
import pytest

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./mock-fsm.sqlite3")
os.environ.setdefault("DATA_ENCRYPTION_KEY", base64.b64encode(b"f" * 32).decode())
os.environ.setdefault("JWT_SECRET", "mock-fsm-jwt-secret-change-me-32-chars")
os.environ.setdefault("N8N_SHARED_SECRET", "mock-fsm-secret")

from app.database import Base, engine
from app.main import app
from app.routers import fsm_webhooks
from app.config import get_settings

get_settings().meta_access_token = ""


@pytest.mark.asyncio
async def test_mock_order_whatsapp_gps_upsell_and_store_sync(monkeypatch):
    get_settings().n8n_shared_secret = "mock-fsm-secret"
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    sent = []
    synced = []

    async def fake_send(phone, body):
        sent.append({"phone": phone, "body": body})
        return {"sent": True, "mock": True}

    async def fake_sync(order, event):
        synced.append({"event": event, "address": order.address_data, "status": order.status.value})
        return {"synced": True, "mock": True}

    monkeypatch.setattr(fsm_webhooks, "send_whatsapp_message", fake_send)
    monkeypatch.setattr(fsm_webhooks, "sync_order_to_store", fake_sync)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        registered = await client.post("/api/auth/register", json={
            "email": "fsm-pilot@example.com", "password": "a-secure-password",
            "full_name": "FSM Pilot", "phone": "+96550000001",
            "store_name": "Mock Kuwait Store", "country_code": "KW", "platform": "custom",
        })
        assert registered.status_code == 201
        store_id = registered.json()["stores"][0]["id"]

        created = await client.post("/api/v1/webhooks/order-created", json={
            "store_id": store_id, "source": "mock-shopify", "order_id": "fsm-001",
            "order_number": "FSM-001", "customer_name": "Client Test",
            "customer_phone": "+96550000002", "amount": 25, "currency": "KWD",
            "payment_method": "COD", "items": [{"name": "GCC product", "quantity": 1, "price": 25}],
            "shipping": {"city": "Kuwait City", "address": "Block 1"},
        })
        assert created.status_code == 202
        order_id = created.json()["order_id"]

        async def inbound(message):
            response = await client.post("/api/v1/webhooks/whatsapp/messages", json={"messages": [message]})
            assert response.status_code == 202, response.text

        await inbound({"from": "+96550000002", "type": "interactive", "interactive": {"button_reply": {"id": "confirm_order"}}})
        await inbound({"from": "+96550000002", "type": "interactive", "interactive": {"button_reply": {"id": "send_location"}}})
        await inbound({"from": "+96550000002", "type": "location", "location": {"latitude": 29.3759, "longitude": 47.9774}})
        await inbound({"from": "+96550000002", "type": "interactive", "interactive": {"button_reply": {"id": "confirm_address"}}})
        await inbound({"from": "+96550000002", "type": "interactive", "interactive": {"button_reply": {"id": "reject_upsell"}}})

        decision = await client.post("/api/automation/apply-decision", headers={"X-N8N-Secret": "mock-fsm-secret"}, json={
            "order_id": order_id, "action": "confirm_cod", "status": "confirmed",
            "location_required": True, "gps_lat": 29.3759, "gps_lng": 47.9774,
            "customer_message_ar": "تم تأكيد الطلب ومشاركة الموقع.",
        })
        assert decision.status_code == 200, decision.text
        assert decision.json()["dashboard_updated"] is True

    assert len(sent) >= 4
    assert any(item["event"] == "FINAL_STORE_SYNC" for item in synced)
    assert synced[-1]["address"]["formatted_address"] == "29.375900, 47.977400"
