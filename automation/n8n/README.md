# Mujeeb acquisition workflow

1. Import `mujeeb-acquisition-engine.json` into n8n.
2. Create one **Header Auth** credential named `Mujeeb Acquisition Key`:
   - Header: `X-Mujeeb-Acquisition-Key`
   - Value: the same long random value as `ACQUISITION_ADMIN_KEY` in Mujeeb.
3. Select that credential on both HTTP Request nodes after import.
4. Configure `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` only in the Mujeeb API
   environment. Telegram receives qualified prospects and progress; tokens never
   enter the browser or the workflow export.
5. Activate the workflow and POST a maximum of 30 public ecommerce URLs:

```json
{
  "run_id": "kw-pilot-001",
  "country_hint": "KW",
  "urls": ["https://merchant.example"]
}
```

The workflow extracts only public business facts. Mujeeb deduplicates by
canonical website, scores fit transparently, and leaves every prospect in a
reviewable state. It never sends Facebook, Instagram, WhatsApp, or email
messages automatically.
