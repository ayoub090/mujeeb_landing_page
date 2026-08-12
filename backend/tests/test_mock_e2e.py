import base64
import os
from datetime import UTC, datetime

import httpx
import pytest


os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./mock-e2e.sqlite3")
os.environ.setdefault("DATA_ENCRYPTION_KEY", base64.b64encode(b"m" * 32).decode())
os.environ.setdefault("JWT_SECRET", "mock-e2e-jwt-secret-change-me-32-chars")
os.environ.setdefault("N8N_SHARED_SECRET", "mock-n8n-secret")

from app.database import Base, engine
from app.main import app
from app.config import get_settings

get_settings().n8n_shared_secret = "mock-n8n-secret"


@pytest.fixture(autouse=True)
async def reset_database():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    yield


@pytest.mark.asyncio
async def test_pilot_flow_register_order_llm_decision_persists():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        register = await client.post(
            "/api/auth/register",
            json={
                "email": "pilot@example.com",
                "password": "a-secure-password",
                "full_name": "Pilot Merchant",
                "phone": "+966501234567",
                "store_name": "Kuwait Mock Store",
                "country_code": "KW",
                "platform": "custom",
            },
        )
        assert register.status_code == 201, register.text
        store_id = register.json()["stores"][0]["id"]

        key = await client.post(
            "/api/api-keys",
            json={"store_id": store_id, "name": "mock-pilot"},
        )
        assert key.status_code == 201, key.text
        api_key = key.json()["api_key"]

        order = await client.post(
            "/api/orders/custom",
            headers={"X-Mujeeb-API-Key": api_key},
            json={
                "order_id": "mock-order-001",
                "order_number": "M-001",
                "customer_name": "Client Mock",
                "customer_phone": "+96550000000",
                "amount": 39.9,
                "currency": "KWD",
                "payment_method": "COD",
                "items": [{"name": "Mock product", "quantity": 1, "price": 39.9}],
                "shipping_city": "Kuwait City",
                "shipping_address": "Block 1, Street 2",
            },
        )
        assert order.status_code == 202, order.text
        order_id = order.json()["mujeeb_order_id"]

        decision = await client.post(
            "/api/automation/apply-decision",
            headers={"X-N8N-Secret": "mock-n8n-secret"},
            json={
                "order_id": order_id,
                "action": "confirm_cod",
                "status": "confirmed",
                "risk_score": 12,
                "location_required": True,
                "gps_lat": 29.3759,
                "gps_lng": 47.9774,
                "customer_message_ar": "تم تأكيد طلبك وتحديد موقعك.",
                "upsell_offer": {"name": "عرض إضافي", "accepted": False},
            },
        )
        assert decision.status_code == 200, decision.text
        assert decision.json()["dashboard_updated"] is True

        summary = await client.get("/api/orders/summary", params={"store_id": store_id})
        assert summary.status_code == 200, summary.text
        assert summary.json()["confirmed"] == 1
        assert summary.json()["gps_verified_count"] == 1

        orders = await client.get("/api/orders", params={"store_id": store_id})
        assert orders.status_code == 200, orders.text
        assert orders.json()[0]["status"] == "confirmed"
