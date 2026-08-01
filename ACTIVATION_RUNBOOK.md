# Mujeeb activation runbook

## Conversion measurement

Mujeeb records anonymous landing events and server-confirmed lifecycle events in the same `funnel_events` table. The production funnel is:

`page_view → lead_created → signup_completed → store_connected → subscription_activated`

Retrieve a 30-day report with:

```bash
curl -H "X-Mujeeb-Analytics-Key: $ANALYTICS_ADMIN_KEY" \
  "https://api.usemujeeb.com/api/marketing/metrics?days=30"
```

The server event, not a success-page redirect, is the source of truth for signups, connected stores, and paid subscriptions.

## External activation gates

- Creem: create recurring Starter, Growth, and Scale products; configure the three product IDs, API key, and webhook secret. Webhook URL: `https://api.usemujeeb.com/api/payments/webhooks/creem`.
- Salla: configure the client ID/secret, callback URL, webhook secret, and required order/customer/webhook scopes.
- Zid: configure the client ID/secret, callback URL, and webhook Basic Auth secret. Mujeeb registers `order.create` and `order.status.update` after OAuth.
- Shopify: configure the client ID/secret and callback URL. Mujeeb registers `ORDERS_CREATE` and `APP_UNINSTALLED` after OAuth.
- Email: configure SMTP host, credentials, and a verified `SMTP_FROM_EMAIL`. The durable worker sends welcome, 40/50 pilot, and deletion notices.
- Meta: keep `META_EMBEDDED_SIGNUP_ENABLED=false` and `VITE_META_EMBEDDED_SIGNUP_ENABLED=false` until business verification and App Review are complete. Then set both flags to `true` and rebuild the dashboard.

## Privacy lifecycle

Authenticated merchants can download a JSON export. Deletion requires password confirmation, has a seven-day cancellation window, and is executed by the lifecycle worker. Active account data and matching lead/email-job records are removed; encrypted backups follow the published retention cycle.
