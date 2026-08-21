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

## Acquisition Pipeline & Bug Fix
* **Pipeline flow**: Target domain -> `acquisition/app.py` -> Chromium headless scrape -> Ollama `qwen2.5:3b` extraction -> Backend scoring & storage -> Telegram owner alert.
* **Async Event Loop Fix**: ScrapeGraphAI uses an internal asyncio event loop inside Chromium loader. Running `graph.run()` directly inside FastAPI's async handler caused loop collisions. The fix wraps execution with `await asyncio.to_thread(graph.run)`.

## Testing & Quality Gates
* **Backend Pytest**:
  ```bash
  export PYTHONPATH="backend:."
  pytest backend/tests
  ```
  Tests cover core FSM, risk calculations, prospect scoring, address parsing, and acquisition endpoint with thread isolation checks.
* **Frontend Build**:
  ```bash
  cd frontend && npm run build
  ```

## Deployment Workflow
* Deployments run on Hostinger VPS using Docker Compose:
  ```bash
  docker compose -f deploy/docker-compose.production.yml up -d --build
  ```
* Acquisition profile (optional/controlled):
  ```bash
  docker compose -f deploy/docker-compose.production.yml --profile acquisition up -d
  ```

## Security & Operational Constraints
* **NO SECRETS**: Never commit API keys, tokens, or credentials to Git. Use environment variables.
* **DO NOT ENABLE AUTOMATIC PROSPECT OUTREACH UNTIL END-TO-END VALIDATION PASSES.**
* Outbound messages are strictly manual or requires explicit owner approval.
* Scraper only accesses public merchant domains and blocks RFC1918 / private IPs (SSRF protection).

## Next Recommended Tasks
1. Execute controlled end-to-end smoke test on acquisition flow (single test URL -> local Ollama extraction -> Telegram notification).
2. Monitor memory and latency of the local `qwen2.5:3b` model during inference under Docker.
