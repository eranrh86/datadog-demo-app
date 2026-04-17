"""
StockLens Auth Module — Google OAuth + User Management
=======================================================
Drop-in addition to backend-app.py.

HOW TO INTEGRATE
----------------
1. pip install -r requirements-auth.txt
2. Set environment variables (see CONFIG section below)
3. Copy this file alongside backend-app.py  OR  paste sections
   into backend-app.py after the Flask app is created.
4. Call  register_auth_blueprints(app)  after  app = Flask(__name__)

ENVIRONMENT VARIABLES
---------------------
GOOGLE_CLIENT_ID   — from Google Cloud Console (OAuth 2.0 web client)
JWT_SECRET         — random secret, min 32 chars (generate: python -c "import secrets; print(secrets.token_hex(32))")
JWT_EXPIRY_HOURS   — access token lifetime in hours (default: 24)
JWT_REFRESH_DAYS   — refresh token lifetime in days  (default: 30)
USER_DB_PATH       — path to SQLite DB file (default: /tmp/stocklens_users.db)
"""

# ── std lib ──────────────────────────────────────────────────────────────────
import os
import time
import uuid
import sqlite3
import logging
import threading
import functools
import hashlib
import secrets

# ── third-party ──────────────────────────────────────────────────────────────
import jwt                                    # PyJWT
from google.oauth2 import id_token as g_id_token
from google.auth.transport import requests as g_requests
from flask import Blueprint, request, jsonify, g, current_app

logger = logging.getLogger("stocklens.auth")


# ─────────────────────────────────────────────────────────────────────────────
# PASSWORD HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _hash_password(password: str) -> str:
    salt = secrets.token_hex(32)
    h = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 310000)
    return f"{salt}:{h.hex()}"


def _verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, h_hex = stored_hash.split(':', 1)
        h = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 310000)
        return secrets.compare_digest(h.hex(), h_hex)
    except Exception:
        return False

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────

GOOGLE_CLIENT_ID  = os.environ.get("GOOGLE_CLIENT_ID", "")
JWT_SECRET        = os.environ.get("JWT_SECRET", "CHANGE_ME_" + os.urandom(16).hex())
JWT_ALGORITHM     = "HS256"
JWT_EXPIRY_HOURS  = int(os.environ.get("JWT_EXPIRY_HOURS", "24"))
JWT_REFRESH_DAYS  = int(os.environ.get("JWT_REFRESH_DAYS", "30"))
USER_DB_PATH      = os.environ.get("USER_DB_PATH", "/tmp/stocklens_users.db")

if JWT_SECRET.startswith("CHANGE_ME_"):
    logger.warning("JWT_SECRET not set — using ephemeral random secret. Tokens won't survive restarts.")

# ─────────────────────────────────────────────────────────────────────────────
# USER STORAGE  (SQLite — no external DB required)
# ─────────────────────────────────────────────────────────────────────────────

_db_lock = threading.Lock()   # SQLite is not thread-safe in WAL=off by default


def _get_conn() -> sqlite3.Connection:
    """Return a thread-local SQLite connection with row_factory set."""
    conn = sqlite3.connect(USER_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _init_db() -> None:
    """Create tables if they don't exist. Safe to call multiple times."""
    ddl = """
    CREATE TABLE IF NOT EXISTS users (
        id          TEXT PRIMARY KEY,
        email       TEXT UNIQUE NOT NULL,
        name        TEXT NOT NULL DEFAULT '',
        picture     TEXT NOT NULL DEFAULT '',
        google_sub  TEXT UNIQUE,
        created_at  INTEGER NOT NULL,
        updated_at  INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS watchlist (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        symbol      TEXT NOT NULL,
        added_at    INTEGER NOT NULL,
        UNIQUE(user_id, symbol)
    );

    CREATE TABLE IF NOT EXISTS portfolio (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        symbol      TEXT NOT NULL,
        shares      REAL NOT NULL DEFAULT 0,
        avg_cost    REAL,
        notes       TEXT NOT NULL DEFAULT '',
        updated_at  INTEGER NOT NULL,
        UNIQUE(user_id, symbol)
    );
    """
    with _db_lock:
        conn = _get_conn()
        try:
            conn.executescript(ddl)
            conn.commit()

            # Migrations for existing databases — add new columns if absent
            migrations = [
                "ALTER TABLE users ADD COLUMN first_name TEXT DEFAULT ''",
                "ALTER TABLE users ADD COLUMN last_name TEXT DEFAULT ''",
                "ALTER TABLE users ADD COLUMN password_hash TEXT DEFAULT ''",
            ]
            for m in migrations:
                try:
                    conn.execute(m)
                except sqlite3.OperationalError:
                    pass  # Column already exists
            conn.commit()
        finally:
            conn.close()


class UserStore:
    """All DB operations for users, watchlists and portfolios."""

    # ── Users ──

    @staticmethod
    def upsert_from_google(sub: str, email: str, name: str, picture: str) -> dict:
        """Create or update a user identified by their Google subject (sub)."""
        now = int(time.time())
        with _db_lock:
            conn = _get_conn()
            try:
                row = conn.execute(
                    "SELECT * FROM users WHERE google_sub = ?", (sub,)
                ).fetchone()

                if row:
                    conn.execute(
                        "UPDATE users SET email=?, name=?, picture=?, updated_at=? WHERE id=?",
                        (email, name, picture, now, row["id"]),
                    )
                    user_id = row["id"]
                else:
                    user_id = str(uuid.uuid4())
                    conn.execute(
                        "INSERT INTO users (id, email, name, picture, google_sub, created_at, updated_at) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (user_id, email, name, picture, sub, now, now),
                    )
                conn.commit()
                return {"id": user_id, "email": email, "name": name, "picture": picture}
            finally:
                conn.close()

    @staticmethod
    def get_by_id(user_id: str) -> dict | None:
        with _db_lock:
            conn = _get_conn()
            try:
                row = conn.execute(
                    "SELECT id, email, name, picture FROM users WHERE id = ?", (user_id,)
                ).fetchone()
                return dict(row) if row else None
            finally:
                conn.close()

    # ── Watchlist ──

    @staticmethod
    def get_watchlist(user_id: str) -> list[dict]:
        with _db_lock:
            conn = _get_conn()
            try:
                rows = conn.execute(
                    "SELECT symbol, added_at FROM watchlist WHERE user_id = ? ORDER BY added_at DESC",
                    (user_id,),
                ).fetchall()
                return [dict(r) for r in rows]
            finally:
                conn.close()

    @staticmethod
    def add_to_watchlist(user_id: str, symbol: str) -> bool:
        """Returns True if inserted, False if already existed."""
        symbol = symbol.upper().strip()
        now = int(time.time())
        with _db_lock:
            conn = _get_conn()
            try:
                try:
                    conn.execute(
                        "INSERT INTO watchlist (user_id, symbol, added_at) VALUES (?, ?, ?)",
                        (user_id, symbol, now),
                    )
                    conn.commit()
                    return True
                except sqlite3.IntegrityError:
                    return False   # UNIQUE constraint — already in watchlist
            finally:
                conn.close()

    @staticmethod
    def remove_from_watchlist(user_id: str, symbol: str) -> bool:
        """Returns True if a row was deleted."""
        symbol = symbol.upper().strip()
        with _db_lock:
            conn = _get_conn()
            try:
                cur = conn.execute(
                    "DELETE FROM watchlist WHERE user_id = ? AND symbol = ?",
                    (user_id, symbol),
                )
                conn.commit()
                return cur.rowcount > 0
            finally:
                conn.close()

    # ── Portfolio ──

    @staticmethod
    def get_portfolio(user_id: str) -> list[dict]:
        with _db_lock:
            conn = _get_conn()
            try:
                rows = conn.execute(
                    "SELECT symbol, shares, avg_cost, notes, updated_at "
                    "FROM portfolio WHERE user_id = ? ORDER BY symbol",
                    (user_id,),
                ).fetchall()
                return [dict(r) for r in rows]
            finally:
                conn.close()

    @staticmethod
    def upsert_portfolio_holding(
        user_id: str,
        symbol: str,
        shares: float,
        avg_cost: float | None = None,
        notes: str = "",
    ) -> dict:
        symbol = symbol.upper().strip()
        now = int(time.time())
        with _db_lock:
            conn = _get_conn()
            try:
                conn.execute(
                    """
                    INSERT INTO portfolio (user_id, symbol, shares, avg_cost, notes, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(user_id, symbol) DO UPDATE SET
                        shares=excluded.shares,
                        avg_cost=excluded.avg_cost,
                        notes=excluded.notes,
                        updated_at=excluded.updated_at
                    """,
                    (user_id, symbol, shares, avg_cost, notes, now),
                )
                conn.commit()
                return {
                    "symbol": symbol,
                    "shares": shares,
                    "avg_cost": avg_cost,
                    "notes": notes,
                    "updated_at": now,
                }
            finally:
                conn.close()

    @staticmethod
    def remove_portfolio_holding(user_id: str, symbol: str) -> bool:
        symbol = symbol.upper().strip()
        with _db_lock:
            conn = _get_conn()
            try:
                cur = conn.execute(
                    "DELETE FROM portfolio WHERE user_id = ? AND symbol = ?",
                    (user_id, symbol),
                )
                conn.commit()
                return cur.rowcount > 0
            finally:
                conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# JWT HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _issue_access_token(user_id: str) -> str:
    payload = {
        "sub":  user_id,
        "iat":  int(time.time()),
        "exp":  int(time.time()) + JWT_EXPIRY_HOURS * 3600,
        "type": "access",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _issue_refresh_token(user_id: str) -> str:
    payload = {
        "sub":  user_id,
        "iat":  int(time.time()),
        "exp":  int(time.time()) + JWT_REFRESH_DAYS * 86400,
        "type": "refresh",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _decode_token(raw: str, token_type: str = "access") -> dict:
    """
    Decode and validate a JWT.
    Raises jwt.PyJWTError subclasses on any failure (expired, invalid sig, wrong type).
    """
    payload = jwt.decode(raw, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    if payload.get("type") != token_type:
        raise jwt.InvalidTokenError(f"Expected token type '{token_type}', got '{payload.get('type')}'")
    return payload


def _bearer_token() -> str | None:
    """Extract the raw token from  Authorization: Bearer <token>."""
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header[7:]
    return None


# ─────────────────────────────────────────────────────────────────────────────
# AUTH DECORATOR
# ─────────────────────────────────────────────────────────────────────────────

def require_auth(fn):
    """
    Flask route decorator — verifies the Bearer JWT and populates g.user_id.

    Usage:
        @app.route("/api/user/watchlist")
        @require_auth
        def watchlist():
            return jsonify(UserStore.get_watchlist(g.user_id))
    """
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        raw = _bearer_token()
        if not raw:
            return jsonify({"error": "Authorization header missing"}), 401
        try:
            payload = _decode_token(raw, token_type="access")
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.PyJWTError as exc:
            logger.warning("JWT validation failed: %s", type(exc).__name__)
            return jsonify({"error": "Invalid token"}), 401

        user_id = payload.get("sub")
        if not user_id:
            return jsonify({"error": "Malformed token"}), 401

        g.user_id = user_id
        return fn(*args, **kwargs)
    return wrapper


# ─────────────────────────────────────────────────────────────────────────────
# GOOGLE ID TOKEN VERIFIER
# ─────────────────────────────────────────────────────────────────────────────

# Reusable HTTP session for Google's certs endpoint
_google_req = g_requests.Request()


def _verify_google_id_token(raw_id_token: str) -> dict:
    """
    Verify a Google ID token and return the decoded claims.
    Raises ValueError on failure (invalid token, wrong audience, expired, etc.).
    """
    if not GOOGLE_CLIENT_ID:
        raise ValueError("GOOGLE_CLIENT_ID env var is not set")

    try:
        claims = g_id_token.verify_oauth2_token(
            raw_id_token,
            _google_req,
            GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=10,   # tolerate minor clock drift
        )
    except Exception as exc:
        # google-auth raises a mix of ValueError and google.auth.exceptions
        raise ValueError(f"Google token verification failed: {exc}") from exc

    # Sanity-check required fields
    for field in ("sub", "email"):
        if field not in claims:
            raise ValueError(f"Google token missing required field: {field}")

    if not claims.get("email_verified", False):
        raise ValueError("Google account email is not verified")

    return claims


# ─────────────────────────────────────────────────────────────────────────────
# BLUEPRINTS
# ─────────────────────────────────────────────────────────────────────────────

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
user_bp = Blueprint("user", __name__, url_prefix="/api/user")


# ── Auth endpoints ────────────────────────────────────────────────────────────

@auth_bp.route("/google", methods=["POST"])
def google_login():
    """
    POST /auth/google
    Body: { "id_token": "<Google ID token from frontend>" }

    Returns:
        200: { "access_token": "...", "refresh_token": "...", "user": {...} }
        400: { "error": "..." }
        401: { "error": "..." }
    """
    body = request.get_json(silent=True) or {}
    raw_id_token = body.get("id_token", "").strip()

    if not raw_id_token:
        return jsonify({"error": "id_token is required"}), 400

    try:
        claims = _verify_google_id_token(raw_id_token)
    except ValueError as exc:
        logger.warning("Google token rejected: %s", exc)
        return jsonify({"error": "Invalid Google ID token"}), 401

    # Extract profile fields
    sub     = claims["sub"]
    email   = claims["email"]
    name    = claims.get("name", email.split("@")[0])
    picture = claims.get("picture", "")

    user = UserStore.upsert_from_google(sub, email, name, picture)
    logger.info("Google login: user_id=%s email=%s", user["id"], email)

    return jsonify({
        "access_token":  _issue_access_token(user["id"]),
        "refresh_token": _issue_refresh_token(user["id"]),
        "user":          user,
    }), 200


@auth_bp.route("/refresh", methods=["POST"])
def refresh_token():
    """
    POST /auth/refresh
    Authorization: Bearer <refresh_token>

    Returns a new access token.
    """
    raw = _bearer_token()
    if not raw:
        return jsonify({"error": "Authorization header missing"}), 401

    try:
        payload = _decode_token(raw, token_type="refresh")
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Refresh token expired, please log in again"}), 401
    except jwt.PyJWTError as exc:
        logger.warning("Refresh token invalid: %s", type(exc).__name__)
        return jsonify({"error": "Invalid refresh token"}), 401

    user_id = payload.get("sub")
    user = UserStore.get_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "access_token": _issue_access_token(user_id),
        "user":         user,
    }), 200


@auth_bp.route("/me", methods=["GET"])
@require_auth
def get_me():
    """
    GET /auth/me
    Authorization: Bearer <access_token>

    Returns the authenticated user's profile.
    """
    user = UserStore.get_by_id(g.user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": user}), 200


@auth_bp.route("/register", methods=["POST"])
def register():
    """
    POST /auth/register
    Body: { "first_name": "...", "last_name": "...", "email": "...", "password": "..." }

    Returns:
        201: { "jwt": "...", "user": {...} }
        400: { "error": "..." }
        409: { "error": "Email already registered" }
    """
    data = request.get_json(silent=True) or {}
    first_name = (data.get('first_name') or '').strip()
    last_name  = (data.get('last_name')  or '').strip()
    email      = (data.get('email')      or '').strip().lower()
    password   = (data.get('password')   or '')

    if not first_name or not last_name:
        return jsonify({'error': 'First and last name are required'}), 400
    if not email or '@' not in email:
        return jsonify({'error': 'Valid email is required'}), 400
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400

    name = f"{first_name} {last_name}"
    password_hash = _hash_password(password)
    user_id = str(uuid.uuid4())
    now = int(time.time())

    with _db_lock:
        conn = _get_conn()
        try:
            conn.execute(
                "INSERT INTO users (id, email, name, first_name, last_name, picture, google_sub, password_hash, created_at, updated_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?)",
                (user_id, email, name, first_name, last_name, '', None, password_hash, now, now)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            return jsonify({'error': 'Email already registered'}), 409
        finally:
            conn.close()

    user = {'id': user_id, 'email': email, 'name': name, 'first_name': first_name, 'last_name': last_name, 'picture': ''}
    token = _issue_access_token(user_id)
    logger.info("Email registration: user_id=%s email=%s", user_id, email)
    return jsonify({'jwt': token, 'user': user}), 201


@auth_bp.route("/login-email", methods=["POST"])
def login_email():
    """
    POST /auth/login-email
    Body: { "email": "...", "password": "..." }

    Returns:
        200: { "jwt": "...", "user": {...} }
        400: { "error": "..." }
        401: { "error": "..." }
    """
    data = request.get_json(silent=True) or {}
    email    = (data.get('email')    or '').strip().lower()
    password = (data.get('password') or '')

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    with _db_lock:
        conn = _get_conn()
        row = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        conn.close()

    if not row or not row['password_hash']:
        return jsonify({'error': 'Invalid email or password'}), 401

    if not _verify_password(password, row['password_hash']):
        return jsonify({'error': 'Invalid email or password'}), 401

    user = {'id': row['id'], 'email': row['email'], 'name': row['name'],
            'first_name': row['first_name'] if row['first_name'] is not None else '',
            'last_name': row['last_name'] if row['last_name'] is not None else '',
            'picture': row['picture']}
    token = _issue_access_token(row['id'])
    logger.info("Email login: user_id=%s email=%s", row['id'], email)
    return jsonify({'jwt': token, 'user': user})


# ── User data endpoints ───────────────────────────────────────────────────────

@user_bp.route("/watchlist", methods=["GET"])
@require_auth
def get_watchlist():
    """
    GET /api/user/watchlist
    Returns: { "watchlist": [{ "symbol": "TSLA", "added_at": 1713000000 }, ...] }
    """
    items = UserStore.get_watchlist(g.user_id)
    return jsonify({"watchlist": items}), 200


@user_bp.route("/watchlist", methods=["POST"])
@require_auth
def add_to_watchlist():
    """
    POST /api/user/watchlist
    Body: { "symbol": "TSLA" }
    """
    body   = request.get_json(silent=True) or {}
    symbol = body.get("symbol", "").strip().upper()

    if not symbol:
        return jsonify({"error": "symbol is required"}), 400
    if len(symbol) > 16:
        return jsonify({"error": "symbol too long"}), 400

    inserted = UserStore.add_to_watchlist(g.user_id, symbol)
    if not inserted:
        return jsonify({"message": "Already in watchlist", "symbol": symbol}), 200

    logger.info("Watchlist add: user_id=%s symbol=%s", g.user_id, symbol)
    return jsonify({"message": "Added", "symbol": symbol}), 201


@user_bp.route("/watchlist/<symbol>", methods=["DELETE"])
@require_auth
def remove_from_watchlist(symbol: str):
    """
    DELETE /api/user/watchlist/<symbol>
    """
    symbol = symbol.strip().upper()
    if not symbol:
        return jsonify({"error": "symbol is required"}), 400

    deleted = UserStore.remove_from_watchlist(g.user_id, symbol)
    if not deleted:
        return jsonify({"error": "Symbol not in watchlist"}), 404

    logger.info("Watchlist remove: user_id=%s symbol=%s", g.user_id, symbol)
    return jsonify({"message": "Removed", "symbol": symbol}), 200


@user_bp.route("/portfolio", methods=["GET"])
@require_auth
def get_portfolio():
    """
    GET /api/user/portfolio
    Returns: { "portfolio": [{ "symbol": "AAPL", "shares": 10, "avg_cost": 150.0, "notes": "" }, ...] }
    """
    holdings = UserStore.get_portfolio(g.user_id)
    return jsonify({"portfolio": holdings}), 200


@user_bp.route("/portfolio", methods=["POST"])
@require_auth
def add_or_update_portfolio():
    """
    POST /api/user/portfolio
    Body: { "symbol": "AAPL", "shares": 10, "avg_cost": 150.0, "notes": "long-term hold" }
    Creates or fully replaces the holding for that symbol.
    """
    body = request.get_json(silent=True) or {}

    symbol = body.get("symbol", "").strip().upper()
    if not symbol:
        return jsonify({"error": "symbol is required"}), 400
    if len(symbol) > 16:
        return jsonify({"error": "symbol too long"}), 400

    try:
        shares = float(body.get("shares", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "shares must be a number"}), 400

    if shares < 0:
        return jsonify({"error": "shares must be >= 0"}), 400

    avg_cost_raw = body.get("avg_cost")
    avg_cost = None
    if avg_cost_raw is not None:
        try:
            avg_cost = float(avg_cost_raw)
            if avg_cost < 0:
                raise ValueError
        except (TypeError, ValueError):
            return jsonify({"error": "avg_cost must be a non-negative number"}), 400

    notes = str(body.get("notes", ""))[:500]   # cap at 500 chars

    holding = UserStore.upsert_portfolio_holding(
        g.user_id, symbol, shares, avg_cost, notes
    )
    logger.info("Portfolio upsert: user_id=%s symbol=%s shares=%s", g.user_id, symbol, shares)
    return jsonify({"message": "Saved", "holding": holding}), 200


@user_bp.route("/portfolio/<symbol>", methods=["DELETE"])
@require_auth
def remove_portfolio_holding(symbol: str):
    """
    DELETE /api/user/portfolio/<symbol>
    """
    symbol = symbol.strip().upper()
    deleted = UserStore.remove_portfolio_holding(g.user_id, symbol)
    if not deleted:
        return jsonify({"error": "Holding not found"}), 404
    logger.info("Portfolio remove: user_id=%s symbol=%s", g.user_id, symbol)
    return jsonify({"message": "Removed", "symbol": symbol}), 200


# ─────────────────────────────────────────────────────────────────────────────
# REGISTRATION HELPER  (call this from backend-app.py)
# ─────────────────────────────────────────────────────────────────────────────

def register_auth_blueprints(flask_app) -> None:
    """
    Initialize the auth module and register all blueprints with the Flask app.

    Call this right after  app = Flask(__name__)  in backend-app.py:

        from auth_module import register_auth_blueprints
        register_auth_blueprints(app)
    """
    _init_db()
    flask_app.register_blueprint(auth_bp)
    flask_app.register_blueprint(user_bp)
    logger.info(
        "Auth module initialized — DB=%s JWT_EXPIRY=%sh REFRESH=%sd",
        USER_DB_PATH,
        JWT_EXPIRY_HOURS,
        JWT_REFRESH_DAYS,
    )
