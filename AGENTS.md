# AGENTS.md — Mujeeb Project Context & Operational Guide

## Project Overview
**Mujeeb (مجيب)** is an Arabic AI-driven WhatsApp order-confirmation and COD (Cash on Delivery) revenue operations platform for GCC ecommerce merchants (Saudi Arabia, UAE, Kuwait, Bahrain, Qatar, Oman). It integrates with Salla, Zid, and Shopify to confirm orders, verify delivery locations via GPS, prevent RTO (Return to Origin), and trigger fulfillment.

## Architecture & Services
* **Backend API (`backend/`)**: FastAPI (Python 3.11), SQLAlchemy Async (PostgreSQL in production, aiosqlite for local tests), Celery + Redis worker, Alembic migrations. Handles auth, merchant stores, order ingestion, FSM transitions, WAAPI connectors, prospect qualification API, and Telegram alerts.
* **Merchant Dashboard & Admin (`frontend/`)**: React 19, TypeScript, Vite, Tailwind CSS v4, TanStack Query. Provides merchant order pipeline, pilot stats, and internal test tools.
* **Acquisition Extractor (`acquisition/`)**: Isolated FastAPI service running ScrapeGraphAI with local Ollama (`qwen2.5:3b`) LLM for automated, privacy-first qualification of public ecommerce domains.
* **Automation (`automation/n8n/`)**: n8n workflows (`mujeeb-acquisition-engine.json`) orchestrating domain extraction, ICP scoring, Mujeeb ingestion, and Telegram notifications.
* **Deployment & Proxy (`deploy/`, `compose.yml`)**: Docker Compose multi-service architecture behind Nginx on Hostinger VPS.

## Key Recent Commits
* `7b1eca1`: Fix compatibility with LangChain / Ollama integration namespaces.
* `fe54ad8`: Automatic pre-warming and model pulling (`qwen2.5:3b`) on first extraction run.
* `9c95049`: Added controlled GCC acquisition engine, transparent ICP scoring, and Telegram alerts.
* `f4fa83f`: Added showcase video modules and demo assets.
* `71a5055`: Finalized zero-friction pilot onboarding, Arabic RTL UI, Salla/Zid API key setup.
* `beb092c`: Fixed event loop collision in acquisition service with `asyncio.to_thread`.

## Acquisition & Commercial Outreach Pipeline
* **Acquisition flow**: Target domain -> `acquisition/app.py` -> Chromium scrape -> Ollama `qwen2.5:3b` extraction -> Backend scoring & storage -> Telegram owner alert.
* **Outreach Cohort 1**: Top 5 qualified Saudi Salla ecommerce stores (Moments, Almadar, Battal Perfumes, Mim Electronic, 1995 Perfumes) with 100/100 ICP score, verified COD and WhatsApp channels.
* **Review & Sending Mechanism**: Personalized Arabic messages sent to owner's Telegram with direct 1-click `wa.me` links for compliant, owner-supervised outreach.

## Testing & Quality Gates
* **Backend Pytest**:
  ```bash
  export PYTHONPATH="backend:."
  pytest backend/tests
  ```
* **Frontend Build**:
  ```bash
  cd frontend && npm run build
  ```

## Security & Operational Constraints
* **NO SECRETS**: Never commit API keys, tokens, or credentials to Git. Use environment variables.
* **DO NOT ENABLE AUTOMATIC PROSPECT OUTREACH UNTIL END-TO-END VALIDATION PASSES.**
* Outbound messages are strictly manual or require explicit owner approval.
* Scraper only accesses public merchant domains and blocks RFC1918 / private IPs (SSRF protection).

## Commercial Outreach States
* `ready` -> `approved` -> `contacted` -> `replied` -> `interested` -> `pilot` -> `won`
