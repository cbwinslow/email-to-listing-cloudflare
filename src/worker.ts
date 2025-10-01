/**
 * File: src/worker.ts
 * Author: cbwinslow & ChatGPT (GPT-5 Thinking)
 * Date: 2025-09-30
 * Summary:
 *   Cloudflare Worker that ingests inbound emails, stores images to R2,
 *   enqueues analysis work (Queues), runs Workers AI (vision + text),
 *   generates CSVs for FB Catalog/eBay/generic, logs in D1, and replies by email.
 *   Optional: live comps (eBay Browse API), direct eBay Inventory posting,
 *   and Stripe mini-pages for direct checkout.
 *
 * Inputs:
 *   - Inbound Email event (Email Workers)
 *   - HTTP: POST /test, GET /s/:sku, POST /checkout/:sku
 *   - Queues consumer for analysis
 *
 * Security:
 *   - allowlist KV (`allowed_senders`), attachment denylist, no secrets in logs
 *
 * Note:
 *   - eBay posting and Stripe are behind feature flags and secrets.
 */

export interface Env {
  AI: AiBinding;
  ITEMS_BUCKET: R2Bucket;
  DB: D1Database;
  SETTINGS_KV: KVNamespace;
  ANALYSIS_QUEUE: Queue;
  FROM_ADDRESS: string;
  REPLY_DISPLAY_NAME: string;
  DEFAULT_CURRENCY: string;
  DEFAULT_LOCALE: string;
  PUBLIC_BASE_URL: string;
  ALLOW_EBAY_POST?: string;
  ALLOW_STRIPE?: string;
  EMAIL?: EmailSenderBinding; // Cloudflare Email Service (if available)
  EBAY_OAUTH_TOKEN?: string;
  EBAY_ENV?: string;
  EBAY_MARKETPLACE_ID?: string;
  EBAY_SHIP_FROM_POSTAL?: string;
  EBAY_SHIP_FROM_COUNTRY?: string;
  EBAY_LISTING_FORMAT?: string;
  STRIPE_SECRET?: string;
}

type EmailAttachment = { filename: string; contentType: string; data: ArrayBuffer };
type InboundEmail = {
  id: string;
  from: { address: string; name?: string };
  to: { address: string }[];
  subject?: string;
  text?: string;
  html?: string;
  attachments: EmailAttachment[];
  receivedAt: number;
};

type AnalysisResult = {
  title: string;
  condition: "New" | "Open Box" | "Used - Like New" | "Used - Good" | "Used - Fair" | "For parts";
  category: string;
  brand?: string;
  model?: string;
  color?: string;
  attributes: Record<string, string>;
  issues?: string[];
  description: string;
  pricing: {
    suggestedPrice: number;
    compRange?: { low: number; high: number };
    rationale: string;
    comps?: Array<{ title: string; price: number; url?: string }>;
  };
  images: string[];
};

const JSON_CT = { "content-type": "application/json" };

function csvEscape(val: string | number | undefined | null): string {
  const s = val == null ? "" : String(val);
  return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

function sanitizeName(name: string): string {
  return name.replace(/[^a-zA-Z0-9._-]+/g, "_").slice(0, 128);
}

function isSafeAttachment(att: EmailAttachment): boolean {
  const bad = ["application/x-msdownload", "application/x-msdos-program", "application/x-sh"];
  const ext = att.filename.toLowerCase().split(".").pop() || "";
  const badExt = ["exe", "bat", "cmd", "sh", "ps1", "msi", "apk"];
  if (bad.includes(att.contentType)) return false;
  if (badExt.includes(ext)) return false;
  return true;
}

function r2PublicUrl(key: string): string {
  return `https://r2.cloudflarestorage.com/EMAIL-LISTINGS/${encodeURIComponent(key)}`;
}

async function allowSender(env: Env, email: string): Promise<boolean> {
  const allowList = (await env.SETTINGS_KV.get("allowed_senders")) || "";
  if (!allowList) return true;
  const allowed = new Set(allowList.split(/[, \n]+/).filter(Boolean).map(s => s.toLowerCase()));
  const domain = email.split("@")[1]?.toLowerCase();
  return allowed.has(email.toLowerCase()) || (domain ? allowed.has(domain) : false);
}

export default {
  async fetch(req: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    try {
      const url = new URL(req.url);
      // simulate email
      if (req.method === "POST" && url.pathname === "/test") {
        const body = await req.json<any>().catch(() => ({}));
        const fake: InboundEmail = {
          id: crypto.randomUUID(),
          from: { address: body.from || "test@cloudcurio.cc" },
          to: [{ address: env.FROM_ADDRESS }],
          subject: body.subject || "Test Item: Example Guitar Pedal",
          text: body.text || "Boss DS-1 Distortion pedal, lightly used, includes box.",
          html: undefined,
          attachments: [],
          receivedAt: Date.now(),
        };
        await enqueueForAnalysis(env, fake);
        return new Response(JSON.stringify({ ok: true, id: fake.id }), { headers: JSON_CT });
      }

      // Public mini product page
      if (req.method === "GET" && url.pathname.startsWith("/s/")) {
        const sku = decodeURIComponent(url.pathname.split("/s/")[1] || "").trim();
        const row = await env.DB.prepare("SELECT analysis FROM messages WHERE id = ? OR json_extract(analysis, '$.sku') = ?")
          .bind(sku, sku)
          .first<{ analysis: string }>();
        if (!row?.analysis) return new Response("Not found", { status: 404 });
        const a: AnalysisResult & { sku?: string } = JSON.parse(row.analysis);
        const allowStripe = env.ALLOW_STRIPE?.toLowerCase() === "true" && !!env.STRIPE_SECRET;
        const buyButton = allowStripe ? `<form method="POST" action="/checkout/${a["sku"] || sku}"><button>Buy Now</button></form>` : "";
        const html = `<!doctype html><html><head><meta charset="utf-8"><title>${a.title}</title></head>
          <body>
            <h1>${a.title}</h1>
            <p><strong>Price:</strong> ${a.pricing.suggestedPrice} ${env.DEFAULT_CURRENCY}</p>
            <p><em>${a.condition}</em></p>
            ${(a.images || []).slice(0,3).map(u => `<img src="${u}" alt="image" style="max-width:300px;margin:8px">`).join("")}
            <p>${a.description}</p>
            ${buyButton}
          </body></html>`;
        return new Response(html, { headers: { "content-type": "text/html; charset=utf-8" } });
      }

      // Stripe checkout
      if (req.method === "POST" && url.pathname.startsWith("/checkout/")) {
        if (!(env.ALLOW_STRIPE?.toLowerCase() === "true" && env.STRIPE_SECRET)) {
          return new Response(JSON.stringify({ error: "Stripe disabled" }), { status: 400, headers: JSON_CT });
        }
        const sku = decodeURIComponent(url.pathname.split("/checkout/")[1] || "").trim();
        const row = await env.DB.prepare("SELECT analysis FROM messages WHERE id = ? OR json_extract(analysis, '$.sku') = ?")
          .bind(sku, sku)
          .first<{ analysis: string }>();
        if (!row?.analysis) return new Response(JSON.stringify({ error: "Not found" }), { status: 404, headers: JSON_CT });
        const a: AnalysisResult & { sku?: string } = JSON.parse(row.analysis);
        const amount = Math.round((a.pricing.suggestedPrice || 0) * 100);
        const session = await fetch("https://api.stripe.com/v1/checkout/sessions", {
          method: "POST",
          headers: {
            "authorization": `Bearer ${env.STRIPE_SECRET}`,
            "content-type": "application/x-www-form-urlencoded",
          },
          body: new URLSearchParams({
            mode: "payment",
            "line_items[0][price_data][currency]": env.DEFAULT_CURRENCY.toLowerCase(),
            "line_items[0][price_data][product_data][name]": a.title,
            "line_items[0][price_data][unit_amount]": String(amount),
            "line_items[0][quantity]": "1",
            success_url: `${env.PUBLIC_BASE_URL}/s/${a["sku"] || sku}?status=success`,
            cancel_url: `${env.PUBLIC_BASE_URL}/s/${a["sku"] || sku}?status=cancel`,
          }),
        }).then(r => r.json<any>());
        if (!session?.url) return new Response(JSON.stringify({ error: "Stripe session error", session }), { status: 500, headers: JSON_CT });
        return Response.redirect(session.url, 302);
      }

      return new Response("OK");
    } catch (e: any) {
      return new Response(JSON.stringify({ error: String(e) }), { status: 500, headers: JSON_CT });
    }
  },

  async queue(batch: MessageBatch<any>, env: Env, ctx: ExecutionContext) {
    for (const msg of batch.messages) {
      try {
        const incoming = msg.body as InboundEmail;
        const result = await analyzeEmail(env, incoming);
        const csvs = await buildAllCSVs(env, incoming.id, result);
        await logToD1(env, incoming, result, csvs);
        await replyToSender(env, incoming, result, csvs);
        if (env.ALLOW_EBAY_POST?.toLowerCase() === "true" && env.EBAY_OAUTH_TOKEN) {
          await postToEbayIfEnabled(env, result, csvs);
        }
        msg.ack();
      } catch (err: any) {
        console.error("queue-error", err?.stack || err);
        msg.retry();
      }
    }
  },

  async email(message: EmailMessage, env: Env, ctx: ExecutionContext) {
    const parsed = await parseInboundEmail(message);
    if (!(await allowSender(env, parsed.from.address))) return;
    await enqueueForAnalysis(env, parsed);
  },
};

async function enqueueForAnalysis(env: Env, inbound: InboundEmail) {
  await env.DB.prepare(
    `INSERT OR REPLACE INTO messages (id, from_addr, to_addr, subject, received_at, status)
     VALUES (?, ?, ?, ?, ?, ?)`
  ).bind(
    inbound.id,
    inbound.from.address,
    inbound.to.map(t => t.address).join(","),
    inbound.subject || null,
    Date.now(),
    "QUEUED"
  ).run();

  const stored: EmailAttachment[] = [];
  for (const att of inbound.attachments || []) {
    if (!isSafeAttachment(att)) continue;
    const key = `inbox/${inbound.id}/${sanitizeName(att.filename || "attachment.bin")}`;
    await env.ITEMS_BUCKET.put(key, att.data, { httpMetadata: { contentType: att.contentType } });
    stored.push({ ...att, data: new TextEncoder().encode(r2PublicUrl(key)).buffer });
  }

  const queued: InboundEmail = { ...inbound, attachments: stored };
  await env.ANALYSIS_QUEUE.send(queued);
}

async function analyzeEmail(env: Env, email: InboundEmail): Promise<AnalysisResult> {
  const text = email.text || "";
  const imgUrls = email.attachments.map(a => new TextDecoder().decode(a.data)).filter(u => /^https?:\/\//.test(u));

  const system = `You are a pro e-commerce listing assistant. Given product photos and a short description, extract:
- Title (<= 80 chars, SEO)
- Condition in {New, Open Box, Used - Like New, Used - Good, Used - Fair, For parts}
- Category path
- Brand, model, color, key attributes
- Defects (array)
- Long sales description (2 paragraphs)
- Pricing suggestion with rationale and optional compRange
Return strict JSON only.`;

  const user = JSON.stringify({
    description: text,
    images: imgUrls,
    locale: env.DEFAULT_LOCALE,
    currency: env.DEFAULT_CURRENCY,
  });

  const resp: any = await env.AI.run("@cf/meta/llama-3.2-11b-vision-instruct", {
    messages: [
      { role: "system", content: system },
      { role: "user", content: [{ type: "text", text: user }, ...imgUrls.map(u => ({ type: "image_url", image_url: u }))] }
    ],
    max_tokens: 900,
  });

  let parsed: Partial<AnalysisResult> = {};
  try {
    const textOut = typeof resp === "string" ? resp : resp?.response || resp?.output_text || JSON.stringify(resp);
    parsed = JSON.parse(textOut);
  } catch {}

  const base: AnalysisResult = {
    title: parsed.title || (email.subject || "Suggested Listing"),
    condition: (parsed.condition as any) || "Used - Good",
    category: parsed.category || "Misc",
    brand: parsed.brand,
    model: parsed.model,
    color: parsed.color,
    attributes: parsed.attributes || {},
    issues: parsed.issues || [],
    description: parsed.description || (email.text || ""),
    pricing: parsed.pricing || { suggestedPrice: 50, rationale: "Default baseline" },
    images: imgUrls,
  };

  // Live comps from eBay Browse API (optional)
  try {
    const token = env.EBAY_OAUTH_TOKEN;
    if (token) {
      const q = encodeURIComponent([base.brand, base.model, base.title].filter(Boolean).join(" ").slice(0, 120) || "item");
      const ebayEnv = (env.EBAY_ENV || "PRODUCTION").toUpperCase();
      const host = ebayEnv === "SANDBOX" ? "api.sandbox.ebay.com" : "api.ebay.com";
      const url = `https://${host}/buy/browse/v1/item_summary/search?q=${q}&limit=10`;
      const data = await fetch(url, {
        headers: { "Authorization": `Bearer ${token}`, "Content-Type": "application/json" },
      }).then(r => r.json<any>());

      const prices: number[] = [];
      const comps: Array<{ title: string; price: number; url?: string }> = [];
      for (const it of data?.itemSummaries || []) {
        const p = Number(it?.price?.value);
        if (!Number.isFinite(p)) continue;
        prices.push(p);
        comps.push({ title: it.title, price: p, url: it?.itemWebUrl });
      }
      if (prices.length) {
        prices.sort((a,b)=>a-b);
        const low = prices[Math.floor(prices.length * 0.2)];
        const high = prices[Math.floor(prices.length * 0.8)];
        base.pricing.compRange = { low, high };
        // If AI price is out of band, nudge toward median
        const median = prices[Math.floor(prices.length/2)];
        if (Math.abs((base.pricing.suggestedPrice || 0) - median) / Math.max(1, median) > 0.5) {
          base.pricing.suggestedPrice = Math.round(median);
          base.pricing.rationale = (base.pricing.rationale || "") + " | Adjusted to median of live comps.";
        }
        base.pricing.comps = comps.slice(0,5);
      }
    }
  } catch (e) {
    console.warn("comps-error", e);
  }

  // attach a SKU equal to id prefix to use on pages
  (base as any).sku = `SKU-${email.id.slice(0,8)}`;
  return base;
}

async function buildAllCSVs(env: Env, msgId: string, a: AnalysisResult) {
  const sku = `SKU-${msgId.slice(0,8)}`;

  const genericHeaders = ["sku","title","price","currency","condition","description","image_link","additional_image_links","brand","model","color","category"];
  const genericRow = [
    sku, a.title, a.pricing.suggestedPrice, env.DEFAULT_CURRENCY, a.condition, a.description,
    a.images[0] || "", a.images.slice(1).join("|"), a.brand || "", a.model || "", a.color || "", a.category || ""
  ].map(csvEscape).join(",");
  const genericCsv = genericHeaders.join(",") + "\n" + genericRow + "\n";

  const fbHeaders = ["id","title","description","availability","condition","price","link","image_link","brand","additional_image_link","google_product_category"];
  const fbRow = [
    sku, a.title, a.description, "in stock", a.condition.toLowerCase(),
    `${a.pricing.suggestedPrice} ${env.DEFAULT_CURRENCY}`,
    `${env.PUBLIC_BASE_URL}/s/${encodeURIComponent(sku)}`,
    a.images[0] || "", a.brand || "", a.images.slice(1).join(","), a.category || ""
  ].map(csvEscape).join(",");
  const fbCsv = fbHeaders.join(",") + "\n" + fbRow + "\n";

  const ebayHeaders = ["sku","title","description","price","currency","condition","brand","image_urls"];
  const ebayRow = [
    sku, a.title, a.description, a.pricing.suggestedPrice, env.DEFAULT_CURRENCY, a.condition, a.brand || "", a.images.join("|")
  ].map(csvEscape).join(",");
  const ebayCsv = ebayHeaders.join(",") + "\n" + ebayRow + "\n";

  const base = `derived/${msgId}`;
  const genericKey = `${base}/generic.csv`;
  const fbKey = `${base}/facebook.csv`;
  const ebayKey = `${base}/ebay.csv`;

  await env.ITEMS_BUCKET.put(genericKey, genericCsv, { httpMetadata: { contentType: "text/csv" } });
  await env.ITEMS_BUCKET.put(fbKey, fbCsv, { httpMetadata: { contentType: "text/csv" } });
  await env.ITEMS_BUCKET.put(ebayKey, ebayCsv, { httpMetadata: { contentType: "text/csv" } });

  return { sku, genericCsvUrl: r2PublicUrl(genericKey), fbCsvUrl: r2PublicUrl(fbKey), ebayCsvUrl: r2PublicUrl(ebayKey) };
}

async function logToD1(env: Env, email: InboundEmail, a: AnalysisResult, csvs: any) {
  await env.DB.prepare(
    `UPDATE messages SET status = ?, analysis = ?, price_cents = ?, currency = ?, retailer_csv_urls = ? WHERE id = ?`
  ).bind(
    "DONE",
    JSON.stringify(a),
    Math.round((a.pricing.suggestedPrice || 0) * 100),
    env.DEFAULT_CURRENCY,
    JSON.stringify(csvs),
    email.id
  ).run();
}

async function replyToSender(env: Env, email: InboundEmail, a: AnalysisResult, csvs: any) {
  const subject = `Listing Ready: ${a.title} (${csvs.sku})`;
  const lines = [
    `Hi ${email.from.address},`,
    "",
    "Here’s the analysis and ready-to-upload listing files:",
    `• Title: ${a.title}`,
    `• Condition: ${a.condition}`,
    `• Category: ${a.category}`,
    a.brand ? `• Brand: ${a.brand}` : "",
    a.model ? `• Model: ${a.model}` : "",
    a.color ? `• Color: ${a.color}` : "",
    `• Price Suggestion: ${a.pricing.suggestedPrice} ${env.DEFAULT_CURRENCY}` + (a.pricing.compRange ? ` (comps: ${a.pricing.compRange.low}-${a.pricing.compRange.high})` : ""),
    "",
    a.pricing.rationale ? ("Rationale:\n" + a.pricing.rationale) : "",
    "",
    "CSV downloads:",
    `• Generic: ${csvs.genericCsvUrl}`,
    `• Facebook Catalog: ${csvs.fbCsvUrl}`,
    `• eBay (helper): ${csvs.ebayCsvUrl}`,
    "",
    env.ALLOW_STRIPE?.toLowerCase() === "true" ? `Direct sale page: ${env.PUBLIC_BASE_URL}/s/${csvs.sku}` : "",
    "— CloudCurio Listings Bot",
  ].filter(Boolean);
  const body = lines.join("\n");

  if (env.EMAIL && "send" in env.EMAIL) {
    await env.EMAIL.send({
      from: { address: env.FROM_ADDRESS, name: env.REPLY_DISPLAY_NAME },
      to: [{ address: email.from.address }],
      subject,
      content: [{ type: "text/plain", value: body }],
    });
    return;
  }
  await fetch("https://api.mailchannels.net/tx/v1/send", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      personalizations: [{ to: [{ email: email.from.address }] }],
      from: { email: env.FROM_ADDRESS, name: env.REPLY_DISPLAY_NAME },
      subject,
      content: [{ type: "text/plain", value: body }],
    }),
  });
}

async function postToEbayIfEnabled(env: Env, a: AnalysisResult, csvs: any) {
  // Minimal illustration (Inventory Item + Offer). In production, add full fulfillment, policies, taxes, etc.
  const token = env.EBAY_OAUTH_TOKEN;
  if (!token) return;
  const ebayEnv = (env.EBAY_ENV || "PRODUCTION").toUpperCase();
  const host = ebayEnv === "SANDBOX" ? "api.sandbox.ebay.com" : "api.ebay.com";

  const sku = (a as any).sku || `SKU-${crypto.randomUUID().slice(0,8)}`;
  const headers = { "Authorization": `Bearer ${token}`, "Content-Type": "application/json" };

  // 1) Create or replace Inventory Item
  const inventoryBody = {
    product: {
      title: a.title,
      description: a.description,
      brand: a.brand,
      aspects: a.attributes,
      imageUrls: a.images,
    },
    condition: (a.condition || "USED_GOOD").toString().replace(/\s+/g, "_").toUpperCase(),
  };
  const invRes = await fetch(`https://${host}/sell/inventory/v1/inventory_item/${encodeURIComponent(sku)}`, {
    method: "PUT",
    headers, body: JSON.stringify(inventoryBody)
  });
  if (!invRes.ok) { console.warn("ebay inventory error", await invRes.text()); return; }

  // 2) Create Offer
  const offerBody = {
    sku,
    marketplaceId: env.EBAY_MARKETPLACE_ID || "EBAY_US",
    format: env.EBAY_LISTING_FORMAT || "FIXED_PRICE",
    availableQuantity: 1,
    pricingSummary: { price: { value: a.pricing.suggestedPrice, currency: env.DEFAULT_CURRENCY } },
    listingDescription: a.description,
    categoryId: undefined, // optionally map a.category to eBay category id
    merchantLocationKey: "default", // requires setup
    shippingOptions: [{ shippingCostType: "FLAT_RATE", shippingServices: [] }],
  };
  const offerRes = await fetch(`https://${host}/sell/inventory/v1/offer`, {
    method: "POST", headers, body: JSON.stringify(offerBody)
  });
  if (!offerRes.ok) { console.warn("ebay offer error", await offerRes.text()); return; }
  const offer = await offerRes.json<any>();

  // 3) Publish Offer
  if (offer?.offerId) {
    const pub = await fetch(`https://${host}/sell/inventory/v1/offer/${offer.offerId}/publish`, {
      method: "POST", headers
    });
    if (!pub.ok) console.warn("ebay publish error", await pub.text());
  }
}

async function parseInboundEmail(msg: EmailMessage): Promise<InboundEmail> {
  const atts: EmailAttachment[] = [];
  for await (const att of msg.rawAttachments()) {
    const buf = await att.arrayBuffer();
    atts.push({ filename: att.filename || "attachment.bin", contentType: att.contentType || "application/octet-stream", data: buf });
  }
  return {
    id: crypto.randomUUID(),
    from: { address: msg.from.address, name: msg.from.name },
    to: msg.to.map(t => ({ address: t.address })),
    subject: msg.headers.get("subject") || undefined,
    text: msg.text,
    html: msg.html,
    attachments: atts,
    receivedAt: Date.now(),
  };
}
