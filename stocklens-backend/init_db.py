#!/usr/bin/env python3
"""
StockLens — Database Initialisation Script
==========================================
Run once (or on every pod start — it's idempotent) to create the schema
and optionally seed demo data.

Usage
-----
# In Docker / k8s init-container or entrypoint:
python init_db.py

# With a custom path (overrides DB_PATH env var):
DB_PATH=/tmp/test.db python init_db.py

# Seed demo user + data for local development:
SEED_DEMO_DATA=1 python init_db.py
"""

import json
import logging
import os
import sys

# Allow running from any working directory.
sys.path.insert(0, os.path.dirname(__file__))

from db import UserDatabase

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("init_db")


def main() -> None:
    db_path = os.environ.get("DB_PATH", "/data/stocklens.db")
    seed_demo = os.environ.get("SEED_DEMO_DATA", "").lower() in ("1", "true", "yes")

    logger.info("Initialising StockLens database at: %s", db_path)

    db = UserDatabase(db_path=db_path)

    # ── 1. Create schema (idempotent) ──────────────────────────────────────────
    db.init_schema()
    logger.info("Schema ready.")

    # ── 2. Optional demo seed data ─────────────────────────────────────────────
    if seed_demo:
        _seed_demo_data(db)

    logger.info("Database initialisation complete.")
    db.close()


def _seed_demo_data(db: UserDatabase) -> None:
    """Insert a demo user with a watchlist, portfolio, and alerts."""

    DEMO_GOOGLE_ID = "demo_google_sub_000001"
    DEMO_EMAIL = "demo@stocklens.dev"

    # Upsert demo user
    user = db.upsert_user(
        google_id=DEMO_GOOGLE_ID,
        email=DEMO_EMAIL,
        name="Demo User",
        picture="https://ui-avatars.com/api/?name=Demo+User&background=4F46E5&color=fff",
    )
    logger.info("Demo user: %s (%s)", user["name"], user["email"])

    # Preferences
    db.update_preferences(
        DEMO_GOOGLE_ID,
        {
            "theme": "dark",
            "currency": "USD",
            "notifications": {"email": True, "push": False},
        },
    )

    # Watchlist
    watchlist_symbols = [
        ("AAPL", 178.50),
        ("MSFT", 415.20),
        ("NVDA", 875.00),
        ("TSLA", 175.00),
        ("AMZN", 185.10),
    ]
    for symbol, price in watchlist_symbols:
        added = db.add_to_watchlist(DEMO_GOOGLE_ID, symbol, added_price=price)
        status = "added" if added else "already present"
        logger.info("  Watchlist %s: %s", symbol, status)

    # Portfolio
    holdings = [
        ("AAPL", 10.0, 165.00),
        ("MSFT", 5.0,  380.00),
        ("NVDA", 2.0,  700.00),
    ]
    for symbol, shares, avg_cost in holdings:
        db.upsert_holding(DEMO_GOOGLE_ID, symbol, shares=shares, avg_cost=avg_cost)
        logger.info("  Portfolio %s: %.2f shares @ $%.2f", symbol, shares, avg_cost)

    # Alerts
    alerts = [
        ("AAPL", "above", 200.00, "AAPL target"),
        ("NVDA", "below", 800.00, "NVDA stop-loss"),
        ("TSLA", "above", 250.00, "TSLA breakout"),
    ]
    for symbol, atype, price, note in alerts:
        alert = db.create_alert(DEMO_GOOGLE_ID, symbol, atype, price, note=note)
        logger.info("  Alert #%d: %s %s $%.2f", alert["id"], symbol, atype, price)

    # Seed earnings whisper cache for a couple of symbols
    for symbol, score in [("AAPL", 87), ("NVDA", 92)]:
        db.cache_earnings_whisper(
            symbol,
            score_data={
                "symbol": symbol,
                "epsWhisperScore": score,
                "epsEstimate": 1.50,
                "epsActual": None,
                "whisperVsEstimate": 0.03,
                "source": "demo_seed",
            },
            ttl_hours=6,
        )
        logger.info("  Cached EW score for %s: %d", symbol, score)

    logger.info("Demo seed complete.")


if __name__ == "__main__":
    main()
