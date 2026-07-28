# Mujeeb Micro-SaaS — low-cost delivery plan

Updated: 2026-07-28. Prices below are public pay-as-you-go list prices and may change. Validate destination, taxes, carrier surcharges, caller-ID rules, and Arabic quality before production.

## Product boundary

Mujeeb sells one outcome: turn an order waiting for fulfillment into one of three states:

1. `confirmed`
2. `cancelled`
3. `human_follow_up`

The merchant chooses the customer channel, carrier, and escalation rules. Mujeeb orchestrates the workflow, records consent and outcome, and returns the result to the merchant.

## Cheapest viable channel strategy

### Default: WhatsApp template or interactive message

Use Meta WhatsApp Cloud API directly where account eligibility and templates permit it. A direct integration avoids adding a CPaaS markup layer. The merchant owns the WhatsApp Business Account and grants Mujeeb scoped access; Mujeeb should not pool every customer under one sender.

### Second: deterministic voice confirmation

Use a short pre-generated Arabic prompt and keypad choices:

- press 1 to confirm;
- press 2 to cancel;
- press 3 or say a request for human follow-up.

This removes the LLM and live TTS from most minutes. Cache one prompt per merchant/language and insert only the minimum order fields. Speech recognition is used only when the customer speaks instead of choosing a key.

### Third: conversational voice fallback

Use a realtime agent only when the order needs a clarification that the deterministic flow cannot handle. Set strict token, time, and turn limits. Escalate instead of improvising on price, returns, or delivery promises.

## Telephony decision

| Option | Public list-price signal | MVP decision |
|---|---:|---|
| Twilio direct to Saudi local | USD 0.1738/min | Too expensive as default |
| Twilio direct to Saudi mobile | USD 0.3122/min | Too expensive as default |
| Twilio BYOC/SIP interface | USD 0.0040/min + customer carrier | Viable adapter |
| Telnyx Voice API | USD 0.002/min + destination SIP-trunk fee | Benchmark adapter; verify Saudi route |
| Plivo Saudi local/mobile outbound | Not supported on current Saudi pricing page | Do not select for Saudi PSTN MVP |

Preferred design: a `TelephonyProvider` interface with `customer_sip`, `twilio_byoc`, and `telnyx` adapters. Start with the carrier/SIP account supplied by the pilot merchant. This minimizes telecom administration, protects the merchant’s caller identity, and avoids locking the product to one provider.

Official references:

- Twilio Saudi Voice and BYOC pricing: https://www.twilio.com/en-us/voice/pricing/sa
- Telnyx Voice API pricing: https://telnyx.com/pricing/voice-api/
- Plivo Saudi Voice pricing and support: https://www.plivo.com/voice/pricing/sa/

## Speech and AI decision

| Layer | MVP choice | Cost control |
|---|---|---|
| TTS | Pre-generated/cached Google standard Arabic voice first | Public price: USD 4 per 1M characters after the free allowance |
| Streaming STT | Deepgram Nova-3 Multilingual only for spoken exceptions | Public PAYG: USD 0.0058/min streaming |
| Business logic | Deterministic state machine | No model cost; auditable |
| Free-form clarification | Small text model with structured tool calls | Hard turn/token limit |
| Premium natural conversation | OpenAI Realtime mini or equivalent after benchmark | Optional, never default |

Do not select a voice vendor from demos alone. Benchmark at least 100 real, consented utterances containing Saudi/Moroccan dialect, names, order numbers, addresses, and code-switching. Measure task accuracy, not subjective voice beauty.

Official references:

- Deepgram pricing: https://deepgram.com/pricing
- Google Cloud TTS pricing: https://cloud.google.com/text-to-speech/pricing/
- OpenAI realtime model pricing: https://developers.openai.com/api/docs/models/gpt-realtime

## MVP architecture on the existing 4 GB VPS

```text
Merchant browser
      |
      v
Nginx + HTTPS
      |
      +--> Web app/API (Node.js + Fastify)
      |       |
      |       +--> PostgreSQL
      |       +--> job queue in PostgreSQL initially
      |       +--> provider adapters
      |              |- WhatsApp Cloud API
      |              |- customer SIP / Twilio BYOC / Telnyx
      |              |- Deepgram STT
      |              `- cached TTS audio
      |
      `--> static landing/blog
```

Use one application container and PostgreSQL on the existing VPS. Do not add Redis, Kubernetes, a GPU, a vector database, or a separate analytics platform for the first pilots. PostgreSQL row locking is enough for a small queue. Add Redis only when measured contention requires it.

## Minimum data model

- `organizations`: merchant, country, timezone, retention policy
- `users`: organization role and magic-link authentication
- `provider_connections`: encrypted references to customer-owned providers
- `orders`: merchant order ID, normalized phone, language, value, state
- `contact_attempts`: channel, consent source, timestamps, provider ID, outcome
- `events`: append-only audit log for state changes
- `webhooks`: provider payload hash, idempotency key, processing state
- `subscriptions`: Creem customer/subscription references and plan

Never store card data. Do not record calls by default. Store only what the merchant needs to prove the contact and decision. Apply a short default retention period and offer deletion/export.

## Pilot workflow

1. Merchant signs a pilot order form and data-processing agreement.
2. Merchant verifies its sender/SIP account and lawful contact basis.
3. Merchant uploads a CSV of 50 orders; no full-store integration required.
4. Mujeeb validates numbers, removes duplicates, and creates queued jobs.
5. Customer receives the merchant-approved message/call.
6. Mujeeb records `confirmed`, `cancelled`, or `human_follow_up`.
7. Merchant exports results and later adds delivery outcome.
8. Dashboard compares pilot results with the agreed baseline.

Only after a successful pilot should we build Salla/Zid webhooks and continuous synchronization.

## Cost model per confirmed order

Track provider costs per attempt, not as one monthly estimate:

`unit cost = channel fee + carrier minutes + STT + TTS + LLM + payment allocation`

`cost per confirmed order = total pilot provider cost / confirmed orders`

For deterministic voice, the dominant cost is normally the carrier route. That is why customer-owned SIP/BYOC and short calls matter more than optimizing a small text-model bill.

## Payment and administrative path

### Validation stage

- Keep the first pilot free and contractually limited to 50 orders.
- Do not promise public self-service billing before compliance and support are ready.
- Use a simple pilot order form, DPA, privacy notice, subprocessor list, and deletion procedure.

### First paid customers

- Use Creem as Merchant of Record if the account and product are approved. Creem states that it handles buyer invoicing and indirect sales taxes/VAT as MoR.
- Creem does not remove the founder’s Moroccan income, business-registration, accounting, or data-protection obligations.
- Stripe’s current official availability list does not include Morocco, so do not design the MVP around a direct Moroccan Stripe account.
- Choose the Moroccan legal form with a local accountant based on expected turnover, liability, export receipts, and staffing. Do not create a foreign company merely to obtain a payment processor before comparing total compliance cost.

Official references:

- Creem MoR terms: https://www.creem.io/terms
- Stripe global availability: https://stripe.com/global

## Data-protection minimum before real customer orders

This is an operational checklist, not legal advice.

- Identify whether the merchant or Mujeeb is controller/processor for each workflow.
- Notify the processing to Morocco’s CNDP before launch as applicable.
- If personal data is hosted or transmitted abroad, assess and file the required transfer request.
- Inform people clearly of identity, purpose, recipients, mandatory/optional fields, and access/rectification/opposition rights.
- Sign processor terms with every API vendor and maintain a subprocessor list.
- Encrypt provider secrets, restrict access by organization, log access, and test deletion.
- Obtain the merchant’s warranty that it has a lawful basis to contact each customer and honor channel preferences/opt-outs.
- Review Saudi telecom, caller-ID, anti-spam, and personal-data obligations with qualified local counsel before scaling Saudi calling.

Official CNDP references:

- Obligations and notification/transfer rules: https://www.cndp.ma/conditions/
- Website compliance guidance: https://www.cndp.ma/conformite-des-sites-web/

## Build order

### Week 1 — usable pilot core

- organization login;
- CSV upload and validation;
- order list and three-state workflow;
- mock provider adapter;
- audit events and export.

### Week 2 — first real channel

- WhatsApp Cloud API adapter;
- template approval workflow;
- signed webhooks and idempotency;
- retry policy and opt-out suppression.

### Week 3 — voice fallback

- customer SIP/BYOC adapter;
- cached Arabic prompt and DTMF flow;
- human escalation;
- provider cost ledger.

### Week 4 — paid beta

- pilot report;
- Creem checkout/webhooks;
- plan/usage limits;
- backups, monitoring, deletion/export;
- DPA, terms, privacy, subprocessors.

## Gates before scaling

- At least three completed pilots.
- A measured pilot-to-paid conversion rate.
- Positive gross margin after carrier/API costs.
- Zero cross-tenant data leakage in tests.
- Webhook replay/idempotency tests pass.
- CNDP and cross-border transfer steps reviewed and completed where required.
- A Saudi telecom/privacy review before automated calling volume increases.
