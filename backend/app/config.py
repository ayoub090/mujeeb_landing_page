from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: Literal["development", "test", "production"] = "development"
    database_url: str = "sqlite+aiosqlite:///./mujeeb.sqlite3"
    redis_url: str = "redis://localhost:6379/0"
    frontend_url: AnyHttpUrl = "http://localhost:5173"
    cookie_domain: str | None = None
    jwt_secret: str = "development-only-change-me-32-characters"
    data_encryption_key: str = ""
    trust_proxy_headers: bool = False
    gcc_only_signups: bool = False
    maxmind_account_id: str = ""
    maxmind_license_key: str = ""

    meta_app_id: str = ""
    meta_app_secret: str = ""
    meta_config_id: str = ""
    meta_graph_version: str = "v23.0"
    meta_webhook_verify_token: str = ""
    meta_waba_id: str = ""
    meta_phone_number_id: str = ""
    meta_access_token: str = ""
    meta_pixel_id: str = ""
    meta_capi_access_token: str = ""
    meta_embedded_signup_redirect_uri: str = ""
    meta_embedded_signup_enabled: bool = False

    google_maps_api_key: str = ""
    n8n_webhook_url: str = ""
    waapi_base_url: AnyHttpUrl = "https://waapi.app/api/v1"
    waapi_api_token: str = ""
    waapi_webhook_base_url: AnyHttpUrl = "https://api.usemujeeb.com/api/waapi/webhooks"

    salla_client_id: str = ""
    salla_client_secret: str = ""
    salla_redirect_uri: str = "http://localhost:8000/api/integrations/salla/callback"
    salla_webhook_secret: str = ""
    zid_client_id: str = ""
    zid_client_secret: str = ""
    zid_redirect_uri: str = "http://localhost:8000/api/integrations/zid/callback"
    zid_webhook_secret: str = ""

    shopify_client_id: str = ""
    shopify_client_secret: str = ""
    shopify_redirect_uri: str = "http://localhost:8000/api/integrations/shopify/callback"
    shopify_api_version: str = "2026-07"
    shopify_scopes: str = "read_orders,read_customers"

    creem_api_key: str = ""
    creem_webhook_secret: str = ""
    creem_api_base: str = "https://test-api.creem.io"
    # Public Creem product IDs for the current GCC launch pricing. These remain
    # overridable through environment variables in production.
    creem_product_starter: str = "prod_2vqJ5mN9UsaIs92R0GGEGT"
    creem_product_growth: str = "prod_7jta2efsRo349gYRj8401C"
    creem_product_scale: str = "prod_6FvTUHYPbiKxTrai4rOZGP"
    app_base_url: AnyHttpUrl = "http://localhost:8000"

    analytics_admin_key: str = ""
    # Super admin email for back-office CRM and diagnostic tools
    internal_admin_email: str = "contact@usemujeeb.com"
    resend_api_key: str = ""
    resend_api_base: str = "https://api.resend.com"
    resend_from_email: str = ""
    resend_from_name: str = "Mujeeb"
    smtp_host: str = ""
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_from_name: str = "Mujeeb"
    smtp_use_tls: bool = True
    privacy_deletion_grace_days: int = Field(default=7, ge=1, le=30)

    # OpenRouter is deliberately optional: the core order pipeline keeps
    # working when the provider is unavailable, while automation can opt in
    # through the authenticated endpoint.
    openrouter_api_key: str = ""
    openrouter_base_url: AnyHttpUrl = "https://openrouter.ai/api/v1"
    openrouter_model: str = "deepseek/deepseek-chat-v3.1"
    openrouter_http_referer: str = "https://usemujeeb.com"
    openrouter_app_name: str = "Mujeeb"
    n8n_shared_secret: str = ""
    acquisition_admin_key: str = ""
    acquisition_scraper_url: AnyHttpUrl = "http://acquisition:8080"
    acquisition_daily_limit: int = Field(default=30, ge=1, le=500)
    acquisition_auto_send_enabled: bool = False
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    evolution_api_url: str = "http://evolution_api:8080"
    evolution_api_key: str = "mujeeb_evo_admin_sec_2026"

    access_token_minutes: int = Field(default=30, ge=5, le=1440)
    refresh_token_days: int = Field(default=14, ge=1, le=90)

    @field_validator("jwt_secret")
    @classmethod
    def strong_production_secret(cls, value: str, info):
        if len(value) < 32:
            raise ValueError("JWT_SECRET must contain at least 32 characters")
        return value

    @property
    def secure_cookies(self) -> bool:
        return self.environment == "production"

    @property
    def frontend_origin(self) -> str:
        return str(self.frontend_url).rstrip("/")


@lru_cache
def get_settings() -> Settings:
    return Settings()
