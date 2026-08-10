from __future__ import annotations

import json
import httpx
from pydantic import BaseModel, Field

from app.config import get_settings


class ParsedAddress(BaseModel):
    is_valid: bool = False
    city: str | None = None
    district: str | None = None
    street: str | None = None
    formatted_address: str | None = None
    missing: list[str] = Field(default_factory=list)


async def reverse_geocode(latitude: float, longitude: float) -> ParsedAddress:
    settings = get_settings()
    if not settings.google_maps_api_key:
        return ParsedAddress(
            is_valid=True,
            formatted_address=f"{latitude:.6f}, {longitude:.6f}",
        )
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"latlng": f"{latitude},{longitude}", "language": "ar", "key": settings.google_maps_api_key},
        )
        response.raise_for_status()
    body = response.json()
    result = (body.get("results") or [{}])[0]
    parts = {
        component.get("types", [""])[0]: component.get("long_name")
        for component in result.get("address_components", [])
    }
    city = parts.get("locality") or parts.get("administrative_area_level_2")
    district = parts.get("sublocality") or parts.get("sublocality_level_1")
    return ParsedAddress(
        is_valid=bool(city and district), city=city, district=district,
        street=parts.get("route"), formatted_address=result.get("formatted_address"),
        missing=[key for key, value in (("city", city), ("district", district)) if not value],
    )


async def parse_manual_address(text: str) -> ParsedAddress:
    """Strict JSON address extraction; deterministic fallback keeps the FSM usable offline."""
    settings = get_settings()
    if settings.openrouter_api_key:
        schema = {
            "type": "object",
            "properties": {
                "is_valid": {"type": "boolean"},
                "city": {"type": ["string", "null"]},
                "district": {"type": ["string", "null"]},
                "street": {"type": ["string", "null"]},
                "formatted_address": {"type": ["string", "null"]},
                "missing": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["is_valid", "city", "district", "street", "formatted_address", "missing"],
            "additionalProperties": False,
        }
        body = {
            "model": settings.openrouter_model,
            "messages": [{"role": "system", "content": "Extract a GCC shipping address. Return only JSON matching the schema."}, {"role": "user", "content": text}],
            "response_format": {"type": "json_schema", "json_schema": {"name": "address", "strict": True, "schema": schema}},
        }
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.openrouter_api_key}"}, json=body,
            )
            response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return ParsedAddress.model_validate(json.loads(content))

    chunks = [part.strip() for part in text.replace("\n", ",").split(",") if part.strip()]
    city = chunks[0] if chunks else None
    district = chunks[1] if len(chunks) > 1 else None
    street = chunks[2] if len(chunks) > 2 else None
    return ParsedAddress(
        is_valid=bool(city and district), city=city, district=district, street=street,
        formatted_address=text, missing=[] if city and district else ["city" if not city else "district"],
    )
