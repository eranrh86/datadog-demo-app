"""
sentiment_engine.py — Kestrel Social Sentiment Pipeline
========================================================
Fetches recent Stocktwits messages for a ticker symbol and scores them
bull/bear using a two-pass strategy:

  Pass 1 — Explicit label:   Stocktwits crowd-sourced Bullish/Bearish tag
  Pass 2 — Keyword fallback: regex word-boundary scan against curated lists

Returns a clean dict ready for the frontend Social Sentiment card.

Usage
-----
    from sentiment_engine import fetch_and_analyze, calculate_sentiment, format_time_ago

    result = fetch_and_analyze("AAPL")
    # {
    #   "bullPct": 62, "bearPct": 38,
    #   "confidence": "high",   # high ≥15 labeled | medium 5-14 | low <5
    #   "sample_size": 20,
    #   "messages": [
    #       {"user": "...", "text": "...", "bull": True, "time_ago": "2h ago",
    #        "url": "https://stocktwits.com/username/message/12345"}
    #   ]
    # }

Dependencies
------------
    pip install requests

Environment variables (all optional)
--------------------------------------
    STOCKTWITS_ACCESS_TOKEN   — OAuth token from https://api.stocktwits.com/developers
                                 Raises per-hour rate limit from 200 → 400 requests.
    STOCKTWITS_FETCH_LIMIT    — Number of messages to fetch (default 30, max 30 for public API)
"""

from __future__ import annotations

import logging
import os
import re
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin

import requests

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
STOCKTWITS_API_BASE = "https://api.stocktwits.com/api/2/"
STOCKTWITS_FETCH_LIMIT = int(os.environ.get("STOCKTWITS_FETCH_LIMIT", "30"))
STOCKTWITS_ACCESS_TOKEN = os.environ.get("STOCKTWITS_ACCESS_TOKEN", "")

# Requests session — reuse TCP connections across calls
_SESSION: requests.Session | None = None

# Browser-like headers that reduce Cloudflare bot-detection friction.
# Stocktwits serves a JS challenge to raw curl calls, but a proper Accept
# header + realistic UA often bypasses it for the JSON API endpoint.
_REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://stocktwits.com/",
    "Origin": "https://stocktwits.com",
}

# ---------------------------------------------------------------------------
# Keyword lists
# ---------------------------------------------------------------------------
# Bullish signals — positive price expectation
BULLISH_KEYWORDS: list[str] = [
    "breakout", "buy", "calls", "moon", "bullish", "support", "accumulate",
    "long", "dip buy", "upgrade", "beat", "strong", "rally", "upside", "hold",
    "bounce", "undervalued", "target", "rip", "gap up", "green", "higher highs",
    "oversold", "recovery", "outperform", "earnings beat",
]

# Bearish signals — negative price expectation
BEARISH_KEYWORDS: list[str] = [
    "puts", "short", "sell", "bearish", "resistance", "overvalued", "downgrade",
    "miss", "weak", "drop", "crash", "correction", "dump", "distribution",
    "breakdown", "overbought", "bubble", "fade", "red", "lower lows",
    "gap down", "earnings miss", "debt", "layoffs", "recall",
]

# Pre-compile patterns for performance — word boundaries prevent false matches
# e.g. "calls" should not fire on "recalls"
_BULL_PATTERNS: list[re.Pattern] = [
    re.compile(r"\b" + re.escape(kw) + r"\b", re.IGNORECASE)
    for kw in BULLISH_KEYWORDS
]
_BEAR_PATTERNS: list[re.Pattern] = [
    re.compile(r"\b" + re.escape(kw) + r"\b", re.IGNORECASE)
    for kw in BEARISH_KEYWORDS
]


# ---------------------------------------------------------------------------
# Core scoring functions (public — importable individually)
# ---------------------------------------------------------------------------

def format_time_ago(created_at_str: str) -> str:
    """
    Convert an ISO-8601 UTC timestamp string to a human-readable relative time.

    Examples
    --------
    "2026-04-17T12:00:00Z"  →  "2h ago"
    "2026-04-14T10:00:00Z"  →  "3d ago"
    "2026-04-03T10:00:00Z"  →  "2w ago"
    Any unparseable input    →  "unknown"
    """
    try:
        # Handle both "Z" suffix and explicit "+00:00" offset
        dt = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta_seconds = int((now - dt).total_seconds())

        if delta_seconds < 60:
            return "just now"
        if delta_seconds < 3_600:          # < 1 hour
            return f"{delta_seconds // 60}m ago"
        if delta_seconds < 86_400:         # < 1 day
            return f"{delta_seconds // 3_600}h ago"
        if delta_seconds < 604_800:        # < 1 week
            return f"{delta_seconds // 86_400}d ago"
        return f"{delta_seconds // 604_800}w ago"
    except (ValueError, TypeError, AttributeError):
        return "unknown"


def _keyword_sentiment(text: str) -> str | None:
    """
    Score a message body using keyword matching.

    Returns "Bullish", "Bearish", or None (insufficient signal).
    Ties go to Bullish (markets have a slight positive bias).
    """
    bull_hits = sum(1 for p in _BULL_PATTERNS if p.search(text))
    bear_hits = sum(1 for p in _BEAR_PATTERNS if p.search(text))

    if bull_hits == 0 and bear_hits == 0:
        return None  # neutral / no signal
    return "Bullish" if bull_hits >= bear_hits else "Bearish"


def calculate_sentiment(messages: list[dict]) -> dict:
    """
    Aggregate a scored message list into summary sentiment metrics.

    Each dict in *messages* must have at minimum:
        _bull  : True (bullish) | False (bearish) | None (no signal)
        _sentiment_source : "explicit" | "keyword" | "none"

    Returns
    -------
    {
        "bullPct": int,               # 0-100, percentage of scored msgs that are bullish
        "bearPct": int,               # 100 - bullPct
        "confidence": str,            # "high" / "medium" / "low"
        "sample_size": int,           # total messages fetched
        "messages_with_sentiment": int  # messages that yielded a bull/bear score
    }

    Confidence tiers
    ----------------
    - "high"   : ≥15 messages with an explicit Stocktwits label
    - "medium" : 5-14 explicit labels
    - "low"    : <5 explicit labels (relies heavily on keyword fallback)
    """
    total = len(messages)
    bull_count = sum(1 for m in messages if m.get("_bull") is True)
    bear_count = sum(1 for m in messages if m.get("_bull") is False)
    scored = bull_count + bear_count

    if scored == 0:
        return {
            "bullPct": 50,
            "bearPct": 50,
            "confidence": "low",
            "sample_size": total,
            "messages_with_sentiment": 0,
        }

    bull_pct = round(bull_count / scored * 100)
    bear_pct = 100 - bull_pct

    explicit_count = sum(
        1 for m in messages if m.get("_sentiment_source") == "explicit"
    )
    if explicit_count >= 15:
        confidence = "high"
    elif explicit_count >= 5:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "bullPct": bull_pct,
        "bearPct": bear_pct,
        "confidence": confidence,
        "sample_size": total,
        "messages_with_sentiment": scored,
    }


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _get_session() -> requests.Session:
    """Return a module-level requests Session (created once, reused)."""
    global _SESSION
    if _SESSION is None:
        _SESSION = requests.Session()
        _SESSION.headers.update(_REQUEST_HEADERS)
    return _SESSION


def _fetch_stocktwits(symbol: str) -> list[dict]:
    """
    Fetch up to STOCKTWITS_FETCH_LIMIT messages from the Stocktwits streams API.

    Endpoint:  GET /api/2/streams/symbol/{SYMBOL}.json
    Docs:      https://api.stocktwits.com/developers/docs/streams

    Raises
    ------
    requests.HTTPError   on non-2xx responses
    requests.Timeout     if the API doesn't respond within 8 s
    ValueError           if the response body is not valid JSON or lacks "messages"
    """
    url = urljoin(STOCKTWITS_API_BASE, f"streams/symbol/{symbol.upper()}.json")
    params: dict[str, Any] = {"limit": STOCKTWITS_FETCH_LIMIT}
    if STOCKTWITS_ACCESS_TOKEN:
        params["access_token"] = STOCKTWITS_ACCESS_TOKEN

    session = _get_session()
    log.debug("Fetching Stocktwits stream: %s params=%s", url, params)

    resp = session.get(url, params=params, timeout=8)
    resp.raise_for_status()

    # Cloudflare challenge returns HTML even on 200 in rare edge cases
    content_type = resp.headers.get("Content-Type", "")
    if "html" in content_type:
        raise ValueError(
            f"Stocktwits returned HTML instead of JSON (Cloudflare challenge). "
            f"Status={resp.status_code}"
        )

    data = resp.json()
    messages = data.get("messages")
    if not isinstance(messages, list):
        raise ValueError(
            f"Unexpected Stocktwits response shape — 'messages' key missing. "
            f"Keys present: {list(data.keys())}"
        )

    return messages


# ---------------------------------------------------------------------------
# Message scoring
# ---------------------------------------------------------------------------

def _score_message(msg: dict) -> dict:
    """
    Score a single Stocktwits message dict and return an enriched copy.

    Scoring priority
    ----------------
    1. Explicit Stocktwits label  (entities.sentiment.basic = "Bullish"|"Bearish")
    2. Keyword fallback on the message body
    3. None  — no classifiable signal

    Added keys (prefixed with _ to distinguish from raw API fields)
    ---------------------------------------------------------------
    _bull              : True | False | None
    _sentiment_source  : "explicit" | "keyword" | "none"
    _time_ago          : human-readable relative time string
    """
    scored = dict(msg)  # shallow copy — don't mutate caller's data

    # --- Extract explicit Stocktwits label ---
    entities = msg.get("entities") or {}
    sentiment_obj = entities.get("sentiment") or {}
    explicit_label: str | None = sentiment_obj.get("basic")  # "Bullish" / "Bearish" / None

    if explicit_label == "Bullish":
        scored["_bull"] = True
        scored["_sentiment_source"] = "explicit"
    elif explicit_label == "Bearish":
        scored["_bull"] = False
        scored["_sentiment_source"] = "explicit"
    else:
        # --- Keyword fallback ---
        body: str = msg.get("body") or ""
        kw_result = _keyword_sentiment(body)
        if kw_result == "Bullish":
            scored["_bull"] = True
            scored["_sentiment_source"] = "keyword"
        elif kw_result == "Bearish":
            scored["_bull"] = False
            scored["_sentiment_source"] = "keyword"
        else:
            scored["_bull"] = None
            scored["_sentiment_source"] = "none"

    scored["_time_ago"] = format_time_ago(msg.get("created_at", ""))
    return scored


def _build_message_output(scored_msg: dict) -> dict:
    """
    Convert an internally-scored message dict into the frontend-facing shape.

    Output shape
    ------------
    {
        "user"     : "TechTrader99",
        "text"     : "AAPL breaking out...",
        "bull"     : True,          # True=bullish, False=bearish, None=neutral
        "time_ago" : "2h ago",
        "url"      : "https://stocktwits.com/TechTrader99/message/591023488"
    }
    """
    user_obj = scored_msg.get("user") or {}
    username = user_obj.get("username") or "unknown"
    msg_id = scored_msg.get("id")

    url = (
        f"https://stocktwits.com/{username}/message/{msg_id}"
        if msg_id else
        f"https://stocktwits.com/{username}"
    )

    return {
        "user": username,
        "text": (scored_msg.get("body") or "").strip(),
        "bull": scored_msg.get("_bull"),          # True | False | None
        "time_ago": scored_msg.get("_time_ago", "unknown"),
        "url": url,
    }


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def fetch_and_analyze(symbol: str) -> dict:
    """
    Fetch recent Stocktwits messages for *symbol* and return a sentiment summary.

    Parameters
    ----------
    symbol : str
        Ticker symbol, e.g. "AAPL", "TSLA", "SPY". Case-insensitive.

    Returns
    -------
    {
        "bullPct"               : int,   # 0-100
        "bearPct"               : int,   # 0-100
        "confidence"            : str,   # "high" | "medium" | "low"
        "sample_size"           : int,   # total messages fetched from API
        "messages_with_sentiment": int,  # messages that yielded a bull/bear score
        "messages"              : list[dict]  # scored messages, bull/bear first
    }

    On any fetch error the function returns a fallback result with
    confidence="low" and an empty messages list, logging the exception.
    """
    symbol = symbol.upper().strip()

    # --- Fetch ---
    try:
        raw_messages = _fetch_stocktwits(symbol)
        log.info("Fetched %d Stocktwits messages for %s", len(raw_messages), symbol)
    except requests.HTTPError as exc:
        log.warning("Stocktwits HTTP error for %s: %s", symbol, exc)
        return _fallback_result(symbol, str(exc))
    except requests.Timeout:
        log.warning("Stocktwits timeout for %s", symbol)
        return _fallback_result(symbol, "API timeout")
    except ValueError as exc:
        log.warning("Stocktwits bad response for %s: %s", symbol, exc)
        return _fallback_result(symbol, str(exc))
    except Exception as exc:  # noqa: BLE001
        log.exception("Unexpected error fetching Stocktwits for %s", symbol)
        return _fallback_result(symbol, str(exc))

    # --- Score each message ---
    scored_messages = [_score_message(m) for m in raw_messages]

    # --- Aggregate ---
    summary = calculate_sentiment(scored_messages)

    # --- Build output messages (put bull/bear scored ones first, then neutral) ---
    bullish_msgs = [m for m in scored_messages if m.get("_bull") is True]
    bearish_msgs = [m for m in scored_messages if m.get("_bull") is False]
    neutral_msgs = [m for m in scored_messages if m.get("_bull") is None]

    # Interleave bull/bear so the feed feels balanced, then append neutral
    interleaved: list[dict] = []
    for b, be in zip(bullish_msgs, bearish_msgs):
        interleaved.extend([b, be])
    # Handle unequal lengths
    longer = bullish_msgs[len(bearish_msgs):] or bearish_msgs[len(bullish_msgs):]
    interleaved.extend(longer)
    ordered = interleaved + neutral_msgs

    output_messages = [_build_message_output(m) for m in ordered]

    return {
        **summary,
        "messages": output_messages,
    }


def _fallback_result(symbol: str, error_detail: str) -> dict:
    """Return a safe zero-state result when the API is unavailable."""
    log.debug("Returning fallback sentiment result for %s — %s", symbol, error_detail)
    return {
        "bullPct": 50,
        "bearPct": 50,
        "confidence": "low",
        "sample_size": 0,
        "messages_with_sentiment": 0,
        "messages": [],
        "error": error_detail,
    }


# ---------------------------------------------------------------------------
# CLI test harness
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import json
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    print(f"\nFetching sentiment for {ticker} ...\n")

    t0 = time.perf_counter()
    result = fetch_and_analyze(ticker)
    elapsed = time.perf_counter() - t0

    # Pretty print summary
    print(f"Bull:        {result['bullPct']}%")
    print(f"Bear:        {result['bearPct']}%")
    print(f"Confidence:  {result['confidence']}")
    print(f"Sample size: {result['sample_size']} messages")
    print(f"Scored:      {result['messages_with_sentiment']} messages")
    if "error" in result:
        print(f"Error:       {result['error']}")
    print(f"Elapsed:     {elapsed:.2f}s")
    print()

    msgs = result.get("messages", [])
    if msgs:
        print(f"Top {min(5, len(msgs))} messages:")
        for m in msgs[:5]:
            label = "BULL" if m["bull"] is True else ("BEAR" if m["bull"] is False else "neut")
            print(f"  [{label}] @{m['user']} ({m['time_ago']}): {m['text'][:80]}")
    else:
        print("No messages returned.")

    # Full JSON dump if -v flag provided
    if "-v" in sys.argv:
        print("\n--- Full JSON ---")
        print(json.dumps(result, indent=2))
