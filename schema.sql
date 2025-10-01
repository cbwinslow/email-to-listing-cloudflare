CREATE TABLE IF NOT EXISTS messages (
  id TEXT PRIMARY KEY,
  from_addr TEXT NOT NULL,
  to_addr TEXT NOT NULL,
  subject TEXT,
  received_at INTEGER NOT NULL,
  status TEXT NOT NULL,
  analysis JSON,
  price_cents INTEGER,
  currency TEXT,
  retailer_csv_urls JSON,
  error TEXT
);
