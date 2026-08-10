from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import (
    auth,
    automation,
    custom_orders,
    fsm_webhooks,
    health,
    integrations,
    marketing,
    orders,
    payments,
    privacy,
    webhooks,
    whatsapp,
)

settings = get_settings()
app = FastAPI(title="Mujeeb API", version="0.1.0", docs_url="/api/docs")
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(
        dict.fromkeys(
            [
                settings.frontend_origin,
                "https://usemujeeb.com",
                "https://www.usemujeeb.com",
            ]
        )
    ),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-CSRF-Token", "X-Mujeeb-Analytics-Key"],
)

for api_router in (
    health.router,
    auth.router,
    orders.router,
    integrations.router,
    whatsapp.router,
    payments.router,
    privacy.router,
    webhooks.router,
    custom_orders.router,
    marketing.router,
    automation.router,
    fsm_webhooks.router,
):
    app.include_router(api_router)
