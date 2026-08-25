"""Super Admin Back-Office CRM & Executive Analytics Router for Mujeeb.
Provides real-time visibility into registered users, active sessions, MRR, subscriptions, and leads.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_user, is_internal_admin
from app.config import get_settings
from app.database import get_session
from app.models import (
    AcquisitionProspect,
    BusinessLead,
    Customer,
    FunnelEvent,
    Order,
    OrderStatus,
    Store,
    Subscription,
    User,
)

router = APIRouter(prefix="/api/admin", tags=["admin_crm"])


async def require_admin_access(
    user: User = Depends(get_current_user),
) -> User:
    """Ensure caller is the authorized platform owner."""
    settings = get_settings()
    configured_admin = settings.internal_admin_email.strip().lower()
    
    if configured_admin and user.email.lower() == configured_admin:
        return user
    if is_internal_admin(user):
        return user
    if not configured_admin and user.is_active:
        return user
        
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Accès réservé exclusivement à l'administrateur Mujeeb.",
    )


@router.get("/overview", dependencies=[Depends(require_admin_access)])
async def get_admin_overview(session: AsyncSession = Depends(get_session)) -> dict[str, Any]:
    """Retrieve executive KPI counters, revenue, and active funnel stats."""
    now = datetime.now(UTC)
    last_24h = now - timedelta(hours=24)

    total_users = await session.scalar(select(func.count(User.id))) or 0
    total_stores = await session.scalar(select(func.count(Store.id))) or 0

    total_orders = await session.scalar(select(func.count(Order.id))) or 0
    confirmed_orders = await session.scalar(
        select(func.count(Order.id)).where(Order.status == OrderStatus.confirmed)
    ) or 0
    total_order_volume_sar = await session.scalar(
        select(func.sum(Order.amount)).where(Order.status == OrderStatus.confirmed)
    ) or 0

    subscriptions = (await session.scalars(select(Subscription))).all()
    plan_prices = {"starter": 299, "growth": 599, "scale": 999, "free": 0}
    mrr = sum(plan_prices.get(sub.plan, 0) for sub in subscriptions if sub.status == "active")
    active_subscribers = sum(1 for sub in subscriptions if sub.plan in ["starter", "growth", "scale"] and sub.status == "active")
    pilot_users = sum(1 for sub in subscriptions if sub.plan == "free" or sub.status == "trial")

    sessions_24h = await session.scalar(
        select(func.count(distinct(FunnelEvent.session_id))).where(FunnelEvent.created_at >= last_24h)
    ) or 0
    total_pageviews_24h = await session.scalar(
        select(func.count(FunnelEvent.id)).where(FunnelEvent.created_at >= last_24h)
    ) or 0

    total_leads = await session.scalar(select(func.count(BusinessLead.id))) or 0
    total_prospects = await session.scalar(select(func.count(AcquisitionProspect.id))) or 0

    return {
        "kpis": {
            "mrr_sar": mrr,
            "arr_sar": mrr * 12,
            "total_users": total_users,
            "total_stores": total_stores,
            "active_paying_subscribers": active_subscribers,
            "free_pilot_users": pilot_users,
            "total_orders_processed": total_orders,
            "confirmed_orders": confirmed_orders,
            "confirmed_volume_sar": float(total_order_volume_sar),
            "sessions_24h": sessions_24h,
            "pageviews_24h": total_pageviews_24h,
            "inbound_leads": total_leads,
            "acquisition_prospects": total_prospects,
        }
    }


@router.get("/users", dependencies=[Depends(require_admin_access)])
async def list_admin_users(
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[dict[str, Any]]:
    """List all registered users with their store profiles, platform, and subscription tier."""
    stmt = (
        select(User)
        .options(
            selectinload(User.stores).selectinload(Store.subscription),
            selectinload(User.stores).selectinload(Store.integrations),
        )
        .order_by(desc(User.created_at))
        .limit(limit)
    )
    users = (await session.scalars(stmt)).all()

    results = []
    for u in users:
        stores_data = []
        for s in u.stores:
            sub = s.subscription
            stores_data.append({
                "id": str(s.id),
                "name": s.name,
                "platform": s.platform.value if hasattr(s.platform, "value") else str(s.platform),
                "currency": s.currency,
                "country_code": s.country_code,
                "is_active": s.is_active,
                "plan": sub.plan if sub else "free",
                "subscription_status": sub.status if sub else "inactive",
                "free_confirmations_remaining": sub.free_confirmations_remaining if sub else 50,
                "orders_count_this_month": sub.orders_count_this_month if sub else 0,
            })
        results.append({
            "id": str(u.id),
            "email": u.email,
            "full_name": u.full_name,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "stores": stores_data,
        })
    return results


@router.get("/sessions", dependencies=[Depends(require_admin_access)])
async def list_live_sessions(
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[dict[str, Any]]:
    """List visitor traffic, sessions, pageviews, and attribution tracking."""
    stmt = (
        select(FunnelEvent)
        .order_by(desc(FunnelEvent.created_at))
        .limit(limit)
    )
    events = (await session.scalars(stmt)).all()

    return [
        {
            "id": str(ev.id),
            "event_name": ev.event_name,
            "session_id": ev.session_id,
            "path": ev.path,
            "source": ev.source,
            "attribution": ev.attribution or {},
            "referrer": ev.referrer,
            "ip_hash": ev.ip_hash[:12] if ev.ip_hash else None,
            "created_at": ev.created_at.isoformat() if ev.created_at else None,
        }
        for ev in events
    ]


@router.get("/subscriptions", dependencies=[Depends(require_admin_access)])
async def list_subscriptions(
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, Any]]:
    """List all billing accounts and subscription statuses."""
    stmt = (
        select(Subscription)
        .options(selectinload(Subscription.store).selectinload(Store.owner))
        .order_by(desc(Subscription.created_at))
    )
    subs = (await session.scalars(stmt)).all()

    plan_pricing = {"starter": "299 SAR/mois", "growth": "599 SAR/mois", "scale": "999 SAR/mois", "free": "0 SAR (Pilote 50 orders)"}

    return [
        {
            "id": str(s.id),
            "store_id": str(s.store_id),
            "store_name": s.store.name if s.store else "Boutique",
            "owner_email": s.store.owner.email if s.store and s.store.owner else "N/A",
            "plan": s.plan,
            "plan_price": plan_pricing.get(s.plan, "Custom"),
            "status": s.status,
            "orders_count_this_month": s.orders_count_this_month,
            "free_confirmations_remaining": s.free_confirmations_remaining,
            "creem_customer_id": s.creem_customer_id,
            "creem_subscription_id": s.creem_subscription_id,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in subs
    ]


@router.get("/leads", dependencies=[Depends(require_admin_access)])
async def list_business_leads(
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[dict[str, Any]]:
    """List demo requests and inbound captured leads."""
    stmt = select(BusinessLead).order_by(desc(BusinessLead.created_at)).limit(limit)
    leads = (await session.scalars(stmt)).all()

    return [
        {
            "id": str(l.id),
            "company": l.company,
            "platform": l.platform,
            "monthly_orders": l.monthly_orders,
            "selected_plan": l.selected_plan,
            "status": l.status,
            "referrer": l.referrer,
            "landing_page": l.landing_page,
            "attribution": l.attribution or {},
            "created_at": l.created_at.isoformat() if l.created_at else None,
        }
        for l in leads
    ]


@router.get("/outreach/config", dependencies=[Depends(require_admin_access)])
async def get_outreach_config(session: AsyncSession = Depends(get_session)) -> dict[str, Any]:
    from app.services.telegram_bot_poller import load_quotas
    from app.services.instagram_outreach import is_authenticated as ig_auth
    
    quotas = load_quotas()
    total_prospects = await session.scalar(select(func.count(AcquisitionProspect.id))) or 0
    ready_prospects = await session.scalar(select(func.count(AcquisitionProspect.id)).where(AcquisitionProspect.status == "ready")) or 0
    contacted_prospects = await session.scalar(select(func.count(AcquisitionProspect.id)).where(AcquisitionProspect.status == "contacted")) or 0

    return {
        "quotas": quotas,
        "stats": {
            "total": total_prospects,
            "ready": ready_prospects,
            "contacted": contacted_prospects,
        },
        "channels": {
            "whatsapp": "Baileys (Actif)",
            "email": "Resend API (Actif)",
            "instagram": "Connecté ✅" if ig_auth() else "En attente ❌",
        }
    }


@router.post("/outreach/config", dependencies=[Depends(require_admin_access)])
async def update_outreach_config(payload: dict[str, Any]) -> dict[str, Any]:
    from app.services.telegram_bot_poller import load_quotas, save_quotas
    quotas = load_quotas()
    for k in ["wa_limit", "email_limit", "ig_limit", "scrape_limit"]:
        if k in payload and isinstance(payload[k], int):
            quotas[k] = payload[k]
    save_quotas(quotas)
    return {"status": "saved", "quotas": quotas}


@router.post("/outreach/launch", dependencies=[Depends(require_admin_access)])
async def trigger_outreach_campaign(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    import asyncio
    from app.services.telegram_bot_poller import load_quotas
    from app.services.multi_channel_outreach import dispatch_custom_outreach
    
    quotas = load_quotas()
    payload = payload or {}
    wa_c = payload.get("wa_count", quotas.get("wa_limit", 10))
    mail_c = payload.get("email_count", quotas.get("email_limit", 30))
    ig_c = payload.get("ig_count", quotas.get("ig_limit", 10))
    
    asyncio.create_task(dispatch_custom_outreach(wa_count=wa_c, email_count=mail_c, ig_count=ig_c))
    return {"status": "launched", "wa": wa_c, "email": mail_c, "ig": ig_c}


@router.post("/outreach/scrape", dependencies=[Depends(require_admin_access)])
async def trigger_scraping_run(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    import asyncio
    from app.services.telegram_bot_poller import load_quotas
    from app.services.daily_scraper import scrape_and_qualify_stores
    
    quotas = load_quotas()
    payload = payload or {}
    count = payload.get("target_count", quotas.get("scrape_limit", 50))
    
    asyncio.create_task(scrape_and_qualify_stores(target_count=count))
    return {"status": "scraping_started", "target_count": count}


@router.post("/outreach/instagram/login", dependencies=[Depends(require_admin_access)])
async def admin_instagram_login(payload: dict[str, Any]) -> dict[str, Any]:
    """Login Instagram account directly from Admin CRM with okgram phone-grade session."""
    from app.services.instagram_outreach import login_instagram
    u = payload.get("username", "").strip()
    p = payload.get("password", "").strip()
    code = payload.get("code")
    if not u or not p:
        raise HTTPException(status_code=400, detail="Identifiant et mot de passe Instagram requis.")
    return login_instagram(u, p, verification_code=code)


@router.post("/outreach/instagram/sessionid", dependencies=[Depends(require_admin_access)])
async def admin_instagram_sessionid(payload: dict[str, Any]) -> dict[str, Any]:
    """Inject raw Instagram sessionid cookie."""
    from app.services.instagram_outreach import login_instagram_by_sessionid
    sid = payload.get("session_id", "").strip()
    if not sid:
        raise HTTPException(status_code=400, detail="Cookie sessionid requis.")
    return login_instagram_by_sessionid(sid)



