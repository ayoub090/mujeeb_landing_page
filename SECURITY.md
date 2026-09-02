# Mujeeb security and incident response policy

Last reviewed: 2 September 2026

## Scope

This policy covers Mujeeb production services, connected ecommerce stores, order data, integration credentials, and the personnel or providers that can access them.

## Preventive controls

- Collect and process only the merchant and customer fields required for order confirmation and fulfilment.
- Encrypt HTTPS traffic in transit and encrypt customer names, phone numbers, shipping addresses, and provider credentials at the application layer before database storage.
- Store production secrets in the deployment environment, never in source control.
- Restrict production and customer-data access to the operator and authorized support activity.
- Use strong passwords and multi-factor authentication where the provider supports it.
- Keep development store records logically separated from merchant records by environment and store ownership.
- Retain provider-managed backups only when they are encrypted and access-controlled.
- Record authenticated lifecycle, privacy, integration, and webhook events needed to investigate access and changes.

## Detection and response

1. Triage a suspected incident immediately and preserve non-sensitive evidence.
2. Revoke affected tokens, sessions, and credentials; isolate the affected integration or service.
3. Determine the stores, records, time window, and providers involved.
4. Restore from a known-good build or encrypted backup when necessary.
5. Notify affected merchants, Shopify, providers, or authorities when required by contract or law.
6. Document the cause, remediation, and follow-up controls before closing the incident.

## Privacy requests

Shopify compliance webhooks are verified before processing. Customer records are anonymized for `customers/redact`; store data is deleted for `shop/redact`; and data-access requests are retained as auditable work items for completion within Shopify's deadline.

Security or privacy reports can be sent to support@usemujeeb.com.
