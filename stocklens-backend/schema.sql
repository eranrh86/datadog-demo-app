-- StockLens SQLite Schema
-- All 5 tables with indexes.
-- Apply via: sqlite3 /data/stocklens.db < schema.sql
-- Or let init_db.py handle it (preferred).

PRAGMA journal_mode = WAL;   -- better concurrent-read performance
PRAGMA foreign_keys = ON;

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. users
-- Primary key is the Google "sub" claim (stable across sessions).
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id          TEXT PRIMARY KEY,                       -- Google user ID (sub)
    email       TEXT UNIQUE NOT NULL,
    name        TEXT,
    picture     TEXT,                                   -- Google profile photo URL
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login  TIMESTAMP,
    preferences TEXT                                    -- JSON blob, e.g. {"theme":"dark","currency":"USD"}
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- ─────────────────────────────────────────────────────────────────────────────
-- 2. watchlist
-- One row per (user, symbol).  added_price lets us show % change since added.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS watchlist (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT    NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    symbol      TEXT    NOT NULL,                       -- e.g. "AAPL"
    added_price REAL,                                   -- price at time of addition
    added_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, symbol)
);

CREATE INDEX IF NOT EXISTS idx_watchlist_user   ON watchlist(user_id);
CREATE INDEX IF NOT EXISTS idx_watchlist_symbol ON watchlist(symbol);

-- ─────────────────────────────────────────────────────────────────────────────
-- 3. portfolio
-- Aggregate position per user per symbol.  avg_cost is the cost basis per share.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS portfolio (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT    NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    symbol      TEXT    NOT NULL,
    shares      REAL    NOT NULL DEFAULT 0,             -- can be fractional
    avg_cost    REAL    NOT NULL DEFAULT 0,             -- cost basis per share (USD)
    updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, symbol)
);

CREATE INDEX IF NOT EXISTS idx_portfolio_user   ON portfolio(user_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_symbol ON portfolio(symbol);

-- ─────────────────────────────────────────────────────────────────────────────
-- 4. alerts
-- Price alerts: fire when symbol crosses threshold in the given direction.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alerts (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       TEXT    NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    symbol        TEXT    NOT NULL,
    alert_type    TEXT    NOT NULL CHECK(alert_type IN ('above', 'below')),
    target_price  REAL    NOT NULL,
    triggered     INTEGER NOT NULL DEFAULT 0,           -- 0=pending, 1=fired
    triggered_at  TIMESTAMP,
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    note          TEXT                                  -- optional label from the user
);

CREATE INDEX IF NOT EXISTS idx_alerts_user            ON alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_alerts_symbol_active   ON alerts(symbol, triggered) WHERE triggered = 0;

-- ─────────────────────────────────────────────────────────────────────────────
-- 5. earnings_whisper_cache
-- TTL cache for EarningsWhispers scores.  Checked before hitting the external API.
-- score_data is a JSON blob with the full API response payload.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS earnings_whisper_cache (
    symbol      TEXT    PRIMARY KEY,
    score_data  TEXT    NOT NULL,                       -- JSON blob
    fetched_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at  TIMESTAMP NOT NULL                      -- computed: fetched_at + TTL
);

CREATE INDEX IF NOT EXISTS idx_ew_cache_expires ON earnings_whisper_cache(expires_at);
