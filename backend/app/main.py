from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import (
    auth,
    custom_orders,
    health,
    integrations,
    orders,
    payments,
    webhooks,
    whatsapp,
)

settings = get_settings()
app = FastAPI(title="Mujeeb API", version="0.1.0", docs_url="/api/docs")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
)

for api_router in (
    health.router,
    auth.router,
    orders.router,
    integrations.router,
    whatsapp.router,
    payments.router,
    webhooks.router,
    custom_orders.router,
):
    app.include_router(api_router)
