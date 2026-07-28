# Mujeeb — Hetzner, domain and free-tier launch plan

## Buy only after validation

Keep the landing page on Vercel until the pilot funnel proves demand. Buy the domain and Hetzner server when at least one of these gates is met:

- 20 qualified free-tier signups, or
- 5 completed pilots, or
- 2 paying customers.

This avoids infrastructure work before market proof.

## Recommended first production setup

- Domain: short brand domain controlled by Mujeeb.
- DNS and edge protection: Cloudflare free plan.
- Compute: one Hetzner Cloud server in Germany, 4 GB RAM minimum for the first pilot cohort.
- Runtime: Docker Compose with reverse proxy, app API, worker, PostgreSQL and Redis.
- TLS: automatic HTTPS through Caddy.
- Backups: encrypted daily database backup, retained for 14 days, plus a monthly restore test.
- Monitoring: uptime, API latency, failed jobs, call completion and error rate.
- Secrets: server-side environment variables; never commit provider keys to GitHub.

## Free tier

- One workspace and one verified business user.
- 50 order-confirmation attempts or 7 days, whichever comes first.
- Dashboard: confirmed, cancelled, unreachable and estimated shipping cost avoided.
- Explicit opt-in for product updates and interview requests.
- Upgrade only after the user sees their own pilot results.

## Funnel events

Track these server-side events with source, medium and campaign:

1. `landing_view`
2. `lead_consent_submitted`
3. `email_verified`
4. `workspace_created`
5. `first_order_imported`
6. `first_confirmation_completed`
7. `pilot_limit_reached`
8. `upgrade_started`
9. `subscription_activated`

Never send customer phone numbers or order contents to analytics tools. Use internal IDs and aggregated counts.

## Legal and trust baseline

- Publish privacy policy and terms before accepting free-tier accounts.
- Record consent text version, timestamp, source and withdrawal status.
- Separate service messages from marketing consent.
- Provide deletion/export request workflow.
- Define retention periods for leads, call recordings, transcripts and order data.
- Execute data-processing agreements with telephony, AI, hosting and email providers.
- Confirm Saudi PDPL and applicable telecom/call-recording requirements with qualified counsel before processing real customer records.

## Migration sequence

1. Buy domain and Hetzner server.
2. Deploy staging and restore a backup test.
3. Connect the custom domain and verify HTTPS.
4. Add the domain property to Google Search Console through DNS.
5. Keep the Vercel URL redirected with a permanent redirect.
6. Submit the new sitemap and monitor indexing.
7. Invite a maximum of five pilot stores.
8. Expand capacity only after reliability and support metrics pass.
