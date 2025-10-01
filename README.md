# Email → Listing on Cloudflare

**Ship date:** 2025-09-30

A Cloudflare Worker that:
- receives emails (with photos) → R2 + Queue
- analyzes with Workers AI (vision + text)
- suggests price + comps (eBay Browse API, optional)
- renders listing CSVs (Meta Catalog, eBay helper, generic)
- replies to the sender with analysis & CSV links
- optionally **posts to eBay** (Inventory/Offers) and **creates Stripe Checkout** mini-pages

## Quickstart
```bash
wrangler d1 create email_to_listing
wrangler kv namespace create SETTINGS_KV
wrangler r2 bucket create email-listings
wrangler queues create email-to-listing-analysis
wrangler queues create email-to-listing-dlq

# Bind IDs in wrangler.toml
wrangler d1 execute email_to_listing --file=./schema.sql
wrangler deploy
```

**Email Routing:** Route `listings@cloudcurio.cc` to this Worker. If Email Service sending isn't enabled on your account, Worker falls back to MailChannels.

## Env / Secrets (recommended via `wrangler secret put`)
- `EBAY_OAUTH_TOKEN` (App or user token with required scopes)
- `EBAY_ENV` (PRODUCTION|SANDBOX)
- `EBAY_MARKETPLACE_ID` (e.g., EBAY_US)
- `EBAY_SHIP_FROM_POSTAL`, `EBAY_SHIP_FROM_COUNTRY`
- `STRIPE_SECRET` (if using Stripe checkout pages)
- KV: `allowed_senders` (comma/space/newline separated)

## Endpoints
- `POST /test` – simulate an inbound email
- `GET  /s/:sku` – public mini product page with Buy button (if Stripe enabled)
- `POST /checkout/:sku` – creates a Stripe Checkout Session (if enabled)

> Toggle features using `ALLOW_EBAY_POST` and `ALLOW_STRIPE` vars.
