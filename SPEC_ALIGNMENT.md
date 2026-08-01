# Mujeeb MVP specification alignment

Product source of truth: `C:\Users\DELL\.gemini\antigravity\scratch\mujeeb-build`.

This file records the deployable interpretation of those specifications. It prevents the public promise, dashboard, API, and operations workflow from drifting apart.

## Live now

- Arabic conversion landing page on `usemujeeb.com` with first-party lead capture and consent.
- React merchant dashboard and FastAPI/PostgreSQL backend.
- Custom store API at `POST /api/orders/custom`, with hashed API keys, encrypted customer data, duplicate protection, risk scoring, and a measured 50-order free pilot.
- Salla and Zid OAuth routes, gated until their production credentials are configured.
- Creem checkout and signed webhook handling, gated until product IDs and secrets are configured.
- Programmatic solution pages plus original Arabic decision guides for SEO/GEO/AEO.
- Deferred marketing pixels and first-party funnel events.
- GCC-specific offer architecture: free 50-order pilot, Starter, Growth, and Scale intent.
- Measured-pilot guarantee and explicit non-guarantee of fabricated revenue outcomes.
- Plan selection captured with each first-party lead for qualification and AOV analysis.

## Explicitly gated

- Customer WhatsApp Embedded Signup remains disabled until Meta business verification and production approval are complete.
- Paid-plan quotas remain unlimited at the API layer until the final commercial limits are approved. The pilot is limited to the first 50 new orders in total; duplicate webhook retries do not consume quota.
- Automated WhatsApp messaging requires explicit opt-in, an approved template when applicable, and official Meta APIs.

## Safety and positioning rules

- Do not publish invented performance statistics, guarantees, customer logos, or testimonials.
- Do not mass-post thin pages or unsolicited promotional comments. Publish original decision-support content and measure qualified actions.
- Store sensitive customer fields encrypted, retain only what the workflow needs, and provide a deletion process before the public paid launch.
- Position Mujeeb around measurable order decisions before fulfillment, not an unverified promise of autonomous voice calling.

## Next production gates

1. Configure and test Salla/Zid production credentials and callbacks.
2. Configure Creem products and verify checkout/webhook events end to end.
3. Complete the customer-data deletion workflow and retention schedule (the public request page is live; backend execution remains operational/manual).
4. Implement onboarding email delivery and the 40/50 upgrade trigger.
5. Add Shopify OAuth and verified webhook subscription.
6. Add server-side Meta CAPI only after the production dataset/token is configured.
7. Enable Embedded Signup only after Meta approval.

## Conversion decisions from the August 2026 re-audit

- The primary ICP is a GCC merchant shipping COD orders on Salla, Zid, Shopify, WooCommerce, or a custom store. The landing page qualifies by platform and monthly order volume.
- Emotional framing is tied to a concrete operational loss: packing, shipping, and team time spent before the customer decision is known.
- Rational proof is the merchant's own 50-order before/after sample, not an invented RTO reduction or a borrowed testimonial.
- Growth is the recommended package for qualified volume, while Pilot removes risk and Scale creates a clear expansion path for multi-store teams.
- The guarantee covers delivery of a measurable pilot and rerunning failures caused by Mujeeb. It never guarantees revenue, RTO, or delivery outcomes.
