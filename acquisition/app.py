import asyncio
import hmac
import ipaddress
import socket
from typing import Any
from urllib.parse import urlsplit

import httpx
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")
    acquisition_admin_key: str = ""
    ollama_model: str = "qwen2.5:3b"
    ollama_base_url: str = "http://ollama:11434"


settings = Settings()
app = FastAPI(title="Mujeeb Acquisition Extractor", docs_url=None, redoc_url=None)
_model_ready = False
_model_lock = asyncio.Lock()


class ExtractInput(BaseModel):
    url: str = Field(min_length=8, max_length=1000)
    country_hint: str | None = Field(default=None, max_length=2)


def _authenticate(value: str | None) -> None:
    if not settings.acquisition_admin_key or not value or not hmac.compare_digest(
        settings.acquisition_admin_key, value
    ):
        raise HTTPException(status_code=401, detail="Acquisition access denied")


def _assert_public_url(value: str) -> str:
    parsed = urlsplit(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise HTTPException(status_code=422, detail="Only public http(s) URLs are supported")
    try:
        addresses = socket.getaddrinfo(parsed.hostname, parsed.port or 443, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise HTTPException(status_code=422, detail="Host cannot be resolved") from exc
    for address in addresses:
        if not ipaddress.ip_address(address[4][0]).is_global:
            raise HTTPException(status_code=422, detail="Private and local targets are blocked")
    return value.strip()


async def _ensure_model() -> None:
    global _model_ready
    if _model_ready:
        return
    async with _model_lock:
        if _model_ready:
            return
        base_url = settings.ollama_base_url.rstrip("/")
        async with httpx.AsyncClient(timeout=httpx.Timeout(1800.0, connect=10.0)) as client:
            tags = await client.get(f"{base_url}/api/tags")
            tags.raise_for_status()
            installed = {item.get("name", "") for item in tags.json().get("models", [])}
            if not any(name == settings.ollama_model or name.startswith(f"{settings.ollama_model}:") for name in installed):
                pull = await client.post(
                    f"{base_url}/api/pull",
                    json={"name": settings.ollama_model, "stream": False},
                )
                pull.raise_for_status()
        _model_ready = True


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "mujeeb-acquisition", "privacy": "local-llm"}


@app.post("/extract")
async def extract(payload: ExtractInput, x_mujeeb_acquisition_key: str | None = Header(default=None)) -> Any:
    _authenticate(x_mujeeb_acquisition_key)
    source = _assert_public_url(payload.url)
    try:
        await _ensure_model()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=503, detail="Local qualification model is not ready") from exc

    # ScrapeGraphAI 1.x still imports ChatOllama from the legacy community
    # namespace, while current LangChain ships it in langchain-ollama.
    import langchain_community.chat_models as community_chat_models
    if not hasattr(community_chat_models, "ChatOllama"):
        from langchain_ollama import ChatOllama
        community_chat_models.ChatOllama = ChatOllama
    from scrapegraphai.graphs import SmartScraperGraph

    graph = SmartScraperGraph(
        prompt="""
Extract only publicly displayed business information from this ecommerce website.
Return one JSON object with exactly these fields: company, website, country_code,
platform, public_email, public_phone, social_profiles, evidence.
country_code must be SA, AE, KW, BH, QA, OM or null.
platform must be salla, zid, shopify, woocommerce, custom, other or null.
social_profiles contains only visible public profile URLs.
evidence contains booleans cod_available and whatsapp_available plus a short reason.
Never infer personal data and return null when information is not public.
""",
        source=source,
        config={
            "llm": {
                "model": f"ollama/{settings.ollama_model}",
                "model_tokens": 8192,
                "format": "json",
                "base_url": settings.ollama_base_url,
            },
            "headless": True,
            "verbose": False,
        },
    )
    result = await asyncio.to_thread(graph.run)
    if not isinstance(result, dict):
        raise HTTPException(status_code=502, detail="Extractor returned an invalid payload")
    result["source_url"] = source
    if payload.country_hint and not result.get("country_code"):
        result["country_code"] = payload.country_hint.upper()
    return result
