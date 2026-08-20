from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import (
    acquisition,
    auth,
    automation,
    custom_orders,
    demo_salla,
    dev_whatsapp,
    fsm_webhooks,
    health,
    integrations,
    marketing,
    orders,
    payments,
    privacy,
    webhooks,
    waapi,
    whatsapp,
)

settings = get_settings()
app = FastAPI(title="Mujeeb API", version="0.1.0", docs_url="/api/docs")
local_origin_pattern = r"^http://(localhost|127\.0\.0\.1):\d+$" if settings.environment != "production" else None
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
    allow_origin_regex=local_origin_pattern,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "X-CSRF-Token",
        "X-Mujeeb-Analytics-Key",
        "X-Mujeeb-Acquisition-Key",
    ],
)

for api_router in (
    health.router,
    acquisition.router,
    auth.router,
    orders.router,
    integrations.router,
    whatsapp.router,
    payments.router,
    privacy.router,
    webhooks.router,
    custom_orders.router,
    demo_salla.router,
    dev_whatsapp.router,
    waapi.router,
    marketing.router,
    automation.router,
    fsm_webhooks.router,
):
    app.include_router(api_router)
