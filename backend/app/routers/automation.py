from __future__ import annotations

import hmac
from typing import Any

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field

from app.config import get_settings
from app.services.llm import LLMNotConfigured, draft_customer_message

router = APIRouter(prefix="/api/automation", tags=["automation"])


class DraftMessageInput(BaseModel):
    # n8n can deliver the webhook body as an object or as a serialized value.
    # Keep the boundary permissive and normalize it before sending to the LLM.
    order: Any = Field(default_factory=dict)
    language: str = Field(default="ar", min_length=2, max_length=8)


@router.post("/draft-message")
async def draft_message(
    payload: DraftMessageInput,
    x_n8n_secret: str | None = Header(default=None),
):
    settings = get_settings()
    if not settings.n8n_shared_secret or not x_n8n_secret or not hmac.compare_digest(
        x_n8n_secret, settings.n8n_shared_secret
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid automation secret")
    try:
        order = payload.order if isinstance(payload.order, dict) else {"raw": payload.order}
        message = await draft_customer_message(order=order, language=payload.language)
    except LLMNotConfigured as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    return {"status": "ok", "message": message, "model": settings.openrouter_model}
