# Mujeeb MVP runbook

## What is implemented

- React/Vite/Tailwind dashboard with GCC onboarding, order overview, risk visibility, integrations and billing.
- FastAPI API with secure cookie sessions, Argon2 passwords and AES-256-GCM encrypted provider tokens.
- Salla and Zid OAuth state validation and server-side token exchange.
- Meta Embedded Signup code exchange; no WhatsApp access token is exposed to the browser.
- Signed, idempotent Meta/Salla/Zid/Creem webhook intake.
- Explainable 0–100 COD risk scoring and optional fail-closed GCC/anonymous-IP signup control.
- PostgreSQL migration, Redis service and Docker Compose deployment package.

## Local launch

1. Copy `backend/.env.example` to `backend/.env` and replace all secrets.
2. Generate `DATA_ENCRYPTION_KEY` as a base64-encoded random 32-byte key.
3. Set `POSTGRES_PASSWORD` in the shell or a root `.env` file.
4. Run `docker compose up --build`.
5. Configure the reverse proxy:
   - `app.usemujeeb.com` → dashboard port 80
   - `api.usemujeeb.com` → API port 8000
6. Run only behind HTTPS in production.

## Provider values still required

- Meta: App ID, App Secret, Embedded Signup Configuration ID, webhook verify token and exact redirect URI.
- Salla: client ID/secret, app-approved scopes, redirect URI and webhook signing secret/contract.
- Zid: client ID/secret, redirect URI and webhook signing secret/contract.
- Creem: API key, webhook secret and product IDs for Starter/Growth/Scale.
- MaxMind: account and license key before enabling `GCC_ONLY_SIGNUPS=true`.

Never paste production secrets into source control. Set them only in EasyPanel/Hostinger secret variables.

## Pre-production gates

- Complete partner review/approval for Meta, Salla and Zid.
- Verify each provider's webhook headers using a real sandbox event; the current configurable HMAC contracts intentionally reject unsigned traffic.
- Configure backups, uptime monitoring and error reporting.
- Replace pilot copy with measured evidence only after enough real orders; do not publish invented conversion or RTO claims.
- Obtain legal review of the PDPL notice, processor terms, retention schedule and marketing consent language.
