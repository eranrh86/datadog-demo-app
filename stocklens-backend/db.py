"""
StockLens — UserDatabase
========================
Thread-safe SQLite layer for user management, watchlists, portfolios,
price alerts, and an earnings-whisper score cache.

All public methods return plain dicts / lists of dicts so they're
trivially JSON-serialisable by Flask.

Usage
-----
from db import UserDatabase
db = UserDatabase()   # defaults to /data/stocklens.db

# On application start (idempotent):
db.init_schema()
"""

import json
import logging
import os
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Path to schema file, expected next to this module.
_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


class UserDatabase:
    """
    Thread-safe SQLite database for StockLens user management.

    Each call acquires a connection from a per-thread pool (threading.local),
    so the same connection is reused within one request but never shared
    across threads — safe with Flask's default threaded server and Gunicorn
    with threaded workers.
    """

    def __init__(self, db_path: str = "/data/stocklens.db") -> None:
        self._db_path = db_path
        self._local = threading.local()  # per-thread connection storage
        self._init_lock = threading.Lock()
        self._ensure_directory()

    # ──────────────────────────────────────────────────────────────────────────
    # Connection management
    # ──────────────────────────────────────────────────────────────────────────

    def _ensure_directory(self) -> None:
        directory = os.path.dirname(self._db_path)
        if directory:
            os.makedirs(directory, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        """Return (and lazily create) the per-thread SQLite connection."""
        if not getattr(self._local, "conn", None):
            conn = sqlite3.connect(
                self._db_path,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
                check_same_thread=False,  # we enforce thread-safety ourselves
            )
            conn.row_factory = sqlite3.Row          # rows behave like dicts
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA busy_timeout = 5000")  # wait up to 5 s on lock
            self._local.conn = conn
        return self._local.conn

    @contextmanager
    def _cursor(self):
        """Context manager: yields a cursor, commits on success, rolls back on error."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()

    def close(self) -> None:
        """Close the calling thread's connection (call from teardown hooks)."""
        conn = getattr(self._local, "conn", None)
        if conn:
            conn.close()
            self._local.conn = None

    # ──────────────────────────────────────────────────────────────────────────
    # Schema initialisation
    # ──────────────────────────────────────────────────────────────────────────

    def init_schema(self) -> None:
        """
        Create all tables (idempotent — uses CREATE TABLE IF NOT EXISTS).
        Safe to call on every app start.
        """
        with self._init_lock:
            if os.path.exists(_SCHEMA_PATH):
                with open(_SCHEMA_PATH, "r") as fh:
                    sql = fh.read()
            else:
                # Inline fallback so the module works without the .sql file.
                sql = _INLINE_SCHEMA

            conn = self._get_connection()
            conn.executescript(sql)
            conn.commit()
            logger.info("StockLens schema initialised at %s", self._db_path)

    # ──────────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _row_to_dict(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
        return dict(row) if row else None

    @staticmethod
    def _rows_to_list(rows) -> List[Dict[str, Any]]:
        return [dict(r) for r in rows]

    @staticmethod
    def _utcnow() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # ──────────────────────────────────────────────────────────────────────────
    # users
    # ──────────────────────────────────────────────────────────────────────────

    def upsert_user(
        self,
        google_id: str,
        email: str,
        name: Optional[str] = None,
        picture: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Insert or update a user record on Google OAuth login.

        Returns the full user row as a dict.
        """
        now = self._utcnow()
        with self._cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (id, email, name, picture, created_at, last_login)
                VALUES (:id, :email, :name, :picture, :now, :now)
                ON CONFLICT(id) DO UPDATE SET
                    email      = excluded.email,
                    name       = excluded.name,
                    picture    = excluded.picture,
                    last_login = excluded.last_login
                """,
                {"id": google_id, "email": email, "name": name, "picture": picture, "now": now},
            )
        return self.get_user(google_id)  # re-fetch to get full row with defaults

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Return user dict or None if not found."""
        with self._cursor() as cur:
            cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            return self._row_to_dict(cur.fetchone())

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Look up a user by email address."""
        with self._cursor() as cur:
            cur.execute("SELECT * FROM users WHERE email = ?", (email,))
            return self._row_to_dict(cur.fetchone())

    def update_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Merge/replace user preferences JSON blob."""
        with self._cursor() as cur:
            cur.execute(
                "UPDATE users SET preferences = ? WHERE id = ?",
                (json.dumps(preferences), user_id),
            )
            return cur.rowcount > 0

    # ──────────────────────────────────────────────────────────────────────────
    # watchlist
    # ──────────────────────────────────────────────────────────────────────────

    def get_watchlist(self, user_id: str) -> List[Dict[str, Any]]:
        """Return all watchlist entries for a user, newest first."""
        with self._cursor() as cur:
            cur.execute(
                """
                SELECT id, symbol, added_price, added_at
                FROM   watchlist
                WHERE  user_id = ?
                ORDER  BY added_at DESC
                """,
                (user_id,),
            )
            return self._rows_to_list(cur.fetchall())

    def add_to_watchlist(
        self,
        user_id: str,
        symbol: str,
        added_price: Optional[float] = None,
    ) -> bool:
        """
        Add symbol to user's watchlist.
        Returns True on success, False if the symbol is already present.
        """
        symbol = symbol.upper().strip()
        try:
            with self._cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO watchlist (user_id, symbol, added_price)
                    VALUES (?, ?, ?)
                    """,
                    (user_id, symbol, added_price),
                )
            return True
        except sqlite3.IntegrityError:
            # UNIQUE constraint: already on watchlist
            return False

    def remove_from_watchlist(self, user_id: str, symbol: str) -> bool:
        """Remove symbol from user's watchlist. Returns True if a row was deleted."""
        symbol = symbol.upper().strip()
        with self._cursor() as cur:
            cur.execute(
                "DELETE FROM watchlist WHERE user_id = ? AND symbol = ?",
                (user_id, symbol),
            )
            return cur.rowcount > 0

    def is_on_watchlist(self, user_id: str, symbol: str) -> bool:
        """Check whether a symbol is on a user's watchlist."""
        symbol = symbol.upper().strip()
        with self._cursor() as cur:
            cur.execute(
                "SELECT 1 FROM watchlist WHERE user_id = ? AND symbol = ?",
                (user_id, symbol),
            )
            return cur.fetchone() is not None

    # ──────────────────────────────────────────────────────────────────────────
    # portfolio
    # ──────────────────────────────────────────────────────────────────────────

    def get_portfolio(self, user_id: str) -> List[Dict[str, Any]]:
        """Return all portfolio holdings for a user."""
        with self._cursor() as cur:
            cur.execute(
                """
                SELECT id, symbol, shares, avg_cost, updated_at
                FROM   portfolio
                WHERE  user_id = ?
                ORDER  BY symbol
                """,
                (user_id,),
            )
            return self._rows_to_list(cur.fetchall())

    def upsert_holding(
        self,
        user_id: str,
        symbol: str,
        shares: float,
        avg_cost: float,
    ) -> bool:
        """
        Insert or replace a portfolio holding.

        Pass shares=0 to effectively zero out a position (position stays in DB).
        Returns True on success.
        """
        symbol = symbol.upper().strip()
        now = self._utcnow()
        with self._cursor() as cur:
            cur.execute(
                """
                INSERT INTO portfolio (user_id, symbol, shares, avg_cost, updated_at)
                VALUES (:user_id, :symbol, :shares, :avg_cost, :now)
                ON CONFLICT(user_id, symbol) DO UPDATE SET
                    shares     = excluded.shares,
                    avg_cost   = excluded.avg_cost,
                    updated_at = excluded.updated_at
                """,
                {
                    "user_id": user_id,
                    "symbol": symbol,
                    "shares": shares,
                    "avg_cost": avg_cost,
                    "now": now,
                },
            )
            return cur.rowcount > 0

    def remove_holding(self, user_id: str, symbol: str) -> bool:
        """Delete a holding row entirely."""
        symbol = symbol.upper().strip()
        with self._cursor() as cur:
            cur.execute(
                "DELETE FROM portfolio WHERE user_id = ? AND symbol = ?",
                (user_id, symbol),
            )
            return cur.rowcount > 0

    # ──────────────────────────────────────────────────────────────────────────
    # alerts
    # ──────────────────────────────────────────────────────────────────────────

    def create_alert(
        self,
        user_id: str,
        symbol: str,
        alert_type: str,
        target_price: float,
        note: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a price alert.

        alert_type must be 'above' or 'below'.
        Returns the new alert row.
        """
        if alert_type not in ("above", "below"):
            raise ValueError("alert_type must be 'above' or 'below'")
        symbol = symbol.upper().strip()
        with self._cursor() as cur:
            cur.execute(
                """
                INSERT INTO alerts (user_id, symbol, alert_type, target_price, note)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, symbol, alert_type, target_price, note),
            )
            alert_id = cur.lastrowid

        with self._cursor() as cur:
            cur.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,))
            return self._row_to_dict(cur.fetchone())

    def get_alerts(
        self,
        user_id: str,
        include_triggered: bool = False,
    ) -> List[Dict[str, Any]]:
        """Return alerts for a user. By default only pending (untriggered) ones."""
        with self._cursor() as cur:
            if include_triggered:
                cur.execute(
                    "SELECT * FROM alerts WHERE user_id = ? ORDER BY created_at DESC",
                    (user_id,),
                )
            else:
                cur.execute(
                    """
                    SELECT * FROM alerts
                    WHERE  user_id = ? AND triggered = 0
                    ORDER  BY created_at DESC
                    """,
                    (user_id,),
                )
            return self._rows_to_list(cur.fetchall())

    def get_pending_alerts_for_symbol(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Return all pending alerts across all users for a given symbol.
        Used by a background price-check job.
        """
        symbol = symbol.upper().strip()
        with self._cursor() as cur:
            cur.execute(
                """
                SELECT * FROM alerts
                WHERE  symbol = ? AND triggered = 0
                """,
                (symbol,),
            )
            return self._rows_to_list(cur.fetchall())

    def mark_alert_triggered(self, alert_id: int) -> bool:
        """Mark an alert as fired. Returns True if the row was updated."""
        now = self._utcnow()
        with self._cursor() as cur:
            cur.execute(
                """
                UPDATE alerts
                SET    triggered = 1, triggered_at = ?
                WHERE  id = ? AND triggered = 0
                """,
                (now, alert_id),
            )
            return cur.rowcount > 0

    def delete_alert(self, user_id: str, alert_id: int) -> bool:
        """Delete an alert, scoped to the owning user."""
        with self._cursor() as cur:
            cur.execute(
                "DELETE FROM alerts WHERE id = ? AND user_id = ?",
                (alert_id, user_id),
            )
            return cur.rowcount > 0

    # ──────────────────────────────────────────────────────────────────────────
    # earnings_whisper_cache
    # ──────────────────────────────────────────────────────────────────────────

    def cache_earnings_whisper(
        self,
        symbol: str,
        score_data: Dict[str, Any],
        ttl_hours: int = 6,
    ) -> None:
        """
        Store (or refresh) an EarningsWhispers score payload.

        score_data is serialised to JSON.  expires_at is set to
        now + ttl_hours in UTC.
        """
        symbol = symbol.upper().strip()
        now = datetime.now(timezone.utc)
        expires_at = (now + timedelta(hours=ttl_hours)).strftime("%Y-%m-%d %H:%M:%S")
        fetched_at = now.strftime("%Y-%m-%d %H:%M:%S")

        with self._cursor() as cur:
            cur.execute(
                """
                INSERT INTO earnings_whisper_cache (symbol, score_data, fetched_at, expires_at)
                VALUES (:symbol, :data, :fetched, :expires)
                ON CONFLICT(symbol) DO UPDATE SET
                    score_data = excluded.score_data,
                    fetched_at = excluded.fetched_at,
                    expires_at = excluded.expires_at
                """,
                {
                    "symbol": symbol,
                    "data": json.dumps(score_data),
                    "fetched": fetched_at,
                    "expires": expires_at,
                },
            )

    def get_cached_earnings_whisper(
        self, symbol: str
    ) -> Optional[Dict[str, Any]]:
        """
        Return cached score data if it exists and has not expired, else None.

        The caller should fetch fresh data from the API when this returns None.
        """
        symbol = symbol.upper().strip()
        now = self._utcnow()
        with self._cursor() as cur:
            cur.execute(
                """
                SELECT score_data, fetched_at, expires_at
                FROM   earnings_whisper_cache
                WHERE  symbol = ? AND expires_at > ?
                """,
                (symbol, now),
            )
            row = cur.fetchone()

        if row is None:
            return None

        try:
            payload = json.loads(row["score_data"])
        except (json.JSONDecodeError, TypeError):
            logger.warning("Corrupted cache entry for %s — ignoring", symbol)
            return None

        return {
            "symbol": symbol,
            "fetched_at": row["fetched_at"],
            "expires_at": row["expires_at"],
            "data": payload,
        }

    def purge_expired_cache(self) -> int:
        """Delete all expired cache entries. Returns count removed."""
        now = self._utcnow()
        with self._cursor() as cur:
            cur.execute(
                "DELETE FROM earnings_whisper_cache WHERE expires_at <= ?", (now,)
            )
            return cur.rowcount


# ──────────────────────────────────────────────────────────────────────────────
# Inline schema fallback (used when schema.sql is not present on disk)
# ──────────────────────────────────────────────────────────────────────────────

_INLINE_SCHEMA = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id          TEXT PRIMARY KEY,
    email       TEXT UNIQUE NOT NULL,
    name        TEXT,
    picture     TEXT,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login  TIMESTAMP,
    preferences TEXT
);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

CREATE TABLE IF NOT EXISTS watchlist (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT    NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    symbol      TEXT    NOT NULL,
    added_price REAL,
    added_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, symbol)
);
CREATE INDEX IF NOT EXISTS idx_watchlist_user   ON watchlist(user_id);
CREATE INDEX IF NOT EXISTS idx_watchlist_symbol ON watchlist(symbol);

CREATE TABLE IF NOT EXISTS portfolio (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT    NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    symbol      TEXT    NOT NULL,
    shares      REAL    NOT NULL DEFAULT 0,
    avg_cost    REAL    NOT NULL DEFAULT 0,
    updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, symbol)
);
CREATE INDEX IF NOT EXISTS idx_portfolio_user   ON portfolio(user_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_symbol ON portfolio(symbol);

CREATE TABLE IF NOT EXISTS alerts (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       TEXT    NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    symbol        TEXT    NOT NULL,
    alert_type    TEXT    NOT NULL CHECK(alert_type IN ('above', 'below')),
    target_price  REAL    NOT NULL,
    triggered     INTEGER NOT NULL DEFAULT 0,
    triggered_at  TIMESTAMP,
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    note          TEXT
);
CREATE INDEX IF NOT EXISTS idx_alerts_user          ON alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_alerts_symbol_active ON alerts(symbol, triggered) WHERE triggered = 0;

CREATE TABLE IF NOT EXISTS earnings_whisper_cache (
    symbol      TEXT    PRIMARY KEY,
    score_data  TEXT    NOT NULL,
    fetched_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at  TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ew_cache_expires ON earnings_whisper_cache(expires_at);
"""
