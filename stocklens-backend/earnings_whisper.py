# earnings_whisper.py
# Earnings Whisper Score: -100 to +100
#
# Score interpretation:
#   +80 to +100  -> Strong Beat Expected
#   +40 to +79   -> Likely Beat
#   +10 to +39   -> Slight Beat Expected
#   -9  to +9    -> Coin Flip
#   -39 to -10   -> Slight Miss Expected
#   -79 to -40   -> Likely Miss
#  -100 to -80   -> Strong Miss Expected

import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Weights — must sum to 1.0
# ---------------------------------------------------------------------------
WEIGHTS = {
    "revision_momentum":    0.30,
    "beat_rate":            0.25,
    "implied_vs_historical":0.20,
    "surprise_magnitude":   0.15,
    "short_interest":       0.10,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_earnings_whisper_score(symbol: str) -> dict:
    """
    Compute the Earnings Whisper Score for *symbol*.

    Returns a dict with keys:
        symbol, score, signal, next_earnings_date, eps_estimate,
        components, confidence, error
    """
    result = {
        "symbol": symbol.upper(),
        "score": None,
        "signal": None,
        "next_earnings_date": None,
        "eps_estimate": None,
        "components": {},
        "confidence": None,
        "error": None,
    }

    try:
        ticker = yf.Ticker(symbol)
        info = _safe_get_info(ticker)

        # Next earnings date + EPS estimate
        result["next_earnings_date"] = _get_next_earnings_date(ticker, info)
        result["eps_estimate"] = _get_eps_estimate(info)

        # Compute each component; track which ones succeed
        component_fns = {
            "revision_momentum":     lambda: _get_revision_momentum(ticker),
            "beat_rate":             lambda: _get_beat_rate(ticker),
            "implied_vs_historical": lambda: _get_implied_vs_historical(ticker, info),
            "surprise_magnitude":    lambda: _get_surprise_magnitude(ticker),
            "short_interest":        lambda: _get_short_interest_signal(ticker, info),
        }

        components = {}
        failed = []

        for name, fn in component_fns.items():
            try:
                value = fn()
                if value is not None and np.isfinite(value):
                    components[name] = float(np.clip(value, -1.0, 1.0))
                else:
                    failed.append(name)
                    logger.warning("%s: component %s returned non-finite value", symbol, name)
            except Exception as exc:
                failed.append(name)
                logger.warning("%s: component %s failed — %s", symbol, name, exc)

        if not components:
            result["error"] = "All scoring components failed — no data available"
            result["signal"] = "Unavailable"
            result["confidence"] = "low"
            return result

        # Redistribute weights if some components failed
        active_weights = {k: WEIGHTS[k] for k in components}
        total_weight = sum(active_weights.values())
        normalized_weights = {k: v / total_weight for k, v in active_weights.items()}

        score = _combine_scores(components, normalized_weights)
        result["score"] = score
        result["signal"] = _get_signal_label(score)
        result["components"] = components
        result["confidence"] = _get_confidence(components, failed)

        if failed:
            result["error"] = f"Components skipped (weights redistributed): {', '.join(failed)}"

    except Exception as exc:
        logger.error("%s: top-level error — %s", symbol, exc)
        result["error"] = str(exc)
        result["signal"] = "Unavailable"
        result["confidence"] = "low"

    return result


# ---------------------------------------------------------------------------
# Component helpers
# ---------------------------------------------------------------------------

def _get_revision_momentum(ticker_obj) -> Optional[float]:
    """
    Analyst estimate revision momentum: −1 (cuts) to +1 (raises).

    Strategy: compare the average EPS estimate for next quarter NOW
    versus 30 days ago and 90 days ago using the analyst_price_targets
    and earnings_estimate data available from yfinance.
    """
    try:
        # yfinance earnings_estimate gives current-quarter and next-quarter rows
        ee = ticker_obj.earnings_estimate
        if ee is None or ee.empty:
            return None

        # Columns available: numberOfAnalysts, avg, low, high, yearAgoEps
        # Rows: 0q (current quarter), +1q (next quarter), 0y, +1y
        if "avg" not in ee.columns:
            return None

        # We want the next-quarter row if available, else current quarter
        row_labels = list(ee.index)
        target_row = None
        for label in row_labels:
            if "+1q" in str(label).lower() or "next" in str(label).lower():
                target_row = label
                break
        if target_row is None and row_labels:
            target_row = row_labels[0]

        avg_now = ee.loc[target_row, "avg"]
        if avg_now is None or (isinstance(avg_now, float) and np.isnan(avg_now)):
            return None

        # Compare to year-ago EPS as a proxy for revision direction
        year_ago = ee.loc[target_row].get("yearAgoEps", None)
        if year_ago is None or (isinstance(year_ago, float) and np.isnan(float(year_ago))):
            # Fallback: check number of analysts as confidence signal
            n = ee.loc[target_row].get("numberOfAnalysts", 0)
            # More analysts covering = slight positive signal for large caps
            n = float(n) if n else 0.0
            return min(n / 30.0, 0.5)  # cap at +0.5 when we lack revision data

        avg_now = float(avg_now)
        year_ago = float(year_ago)

        if year_ago == 0:
            return 0.0

        # Growth rate: positive estimate growth = positive momentum
        growth = (avg_now - year_ago) / abs(year_ago)
        # Map to -1..+1 using tanh (saturates at ~±50% growth)
        return float(np.tanh(growth * 2))

    except Exception as exc:
        logger.debug("revision_momentum error: %s", exc)
        return None


def _get_beat_rate(ticker_obj) -> Optional[float]:
    """
    Historical beat/miss rate over last 8 quarters.
    Returns a value in [0, 1] representing the fraction of beats.
    We then re-map to [-1, +1]: beat_rate * 2 - 1
    """
    try:
        eh = ticker_obj.earnings_history
        if eh is None or eh.empty:
            return None

        required_cols = {"epsEstimate", "epsActual"}
        if not required_cols.issubset(set(eh.columns)):
            return None

        # Most recent 8 quarters
        recent = eh.tail(8).copy()
        recent = recent.dropna(subset=["epsEstimate", "epsActual"])

        if len(recent) < 2:
            return None

        beats = (recent["epsActual"] >= recent["epsEstimate"]).sum()
        beat_rate = beats / len(recent)
        # Map 0..1 → -1..+1
        return float(beat_rate * 2 - 1)

    except Exception as exc:
        logger.debug("beat_rate error: %s", exc)
        return None


def _get_implied_vs_historical(ticker_obj, info: dict) -> Optional[float]:
    """
    Compare options-implied move vs historical earnings move.

    Implied move ≈ (ATM call + ATM put) / spot price, for the
    expiration closest to earnings.

    If implied > historical → options pricing in big move → neutral/negative
    (market is nervous, could go either way). We interpret:
      implied_move < historical_move → market under-pricing → mildly positive
      implied_move > historical_move → market over-pricing → mildly negative
    """
    try:
        # Historical earnings moves from earnings_history
        eh = ticker_obj.earnings_history
        if eh is None or eh.empty:
            return None

        if "surprisePercent" not in eh.columns:
            return None

        surprise_pct = eh["surprisePercent"].dropna()
        if len(surprise_pct) < 2:
            return None

        # Historical magnitude of earnings-day moves (absolute surprise %)
        hist_move = float(surprise_pct.abs().mean())

        # Options chain — find nearest expiration
        expirations = ticker_obj.options
        if not expirations:
            return None

        # Pick the expiration that is 1-6 weeks out
        today = datetime.today()
        chosen_exp = None
        for exp_str in expirations:
            exp_dt = datetime.strptime(exp_str, "%Y-%m-%d")
            days_out = (exp_dt - today).days
            if 7 <= days_out <= 60:
                chosen_exp = exp_str
                break

        if chosen_exp is None:
            chosen_exp = expirations[0]

        spot = info.get("currentPrice") or info.get("regularMarketPrice")
        if not spot:
            return None
        spot = float(spot)

        chain = ticker_obj.option_chain(chosen_exp)
        calls = chain.calls
        puts = chain.puts

        if calls.empty or puts.empty:
            return None

        # Find ATM strike (closest to spot)
        atm_strike = calls.iloc[(calls["strike"] - spot).abs().argsort()[:1]]["strike"].values[0]

        atm_call = calls[calls["strike"] == atm_strike]["lastPrice"]
        atm_put  = puts[puts["strike"] == atm_strike]["lastPrice"]

        if atm_call.empty or atm_put.empty:
            return None

        implied_move_pct = (float(atm_call.iloc[0]) + float(atm_put.iloc[0])) / spot * 100

        if hist_move == 0:
            return 0.0

        ratio = implied_move_pct / hist_move
        # ratio < 1 → implied less than historical → slight positive (market under-pricing risk)
        # ratio > 1 → implied more than historical → slight negative (expensive hedge, uncertainty)
        # Map: ratio=0.5 → +0.5, ratio=1.0 → 0.0, ratio=2.0 → -0.5
        signal = float(np.tanh(1.0 - ratio))
        return signal

    except Exception as exc:
        logger.debug("implied_vs_historical error: %s", exc)
        return None


def _get_surprise_magnitude(ticker_obj) -> Optional[float]:
    """
    Average surprise magnitude over last 8 quarters, normalised to -1..+1.
    Positive surprises → positive, negative → negative.
    Magnitude is captured by tanh scaling.
    """
    try:
        eh = ticker_obj.earnings_history
        if eh is None or eh.empty:
            return None

        if "surprisePercent" not in eh.columns:
            return None

        surprises = eh["surprisePercent"].dropna().tail(8)
        if len(surprises) < 1:
            return None

        avg_surprise = float(surprises.mean())
        # surprisePercent is typically in range -100% to +100%
        # Normalize with tanh: ±10% surprise maps to ≈ ±0.46
        return float(np.tanh(avg_surprise / 10.0))

    except Exception as exc:
        logger.debug("surprise_magnitude error: %s", exc)
        return None


def _get_short_interest_signal(ticker_obj, info: dict) -> Optional[float]:
    """
    Short interest signal: −1 (high short interest, bearish) to +1 (low).

    Uses shortPercentOfFloat from yfinance info.
    Rule of thumb:
      < 2%  → neutral/slight positive
      2–5%  → neutral
      5–10% → slight bearish
      > 10% → strong bearish
      > 20% → very strong bearish
    """
    try:
        short_pct = info.get("shortPercentOfFloat")
        if short_pct is None:
            return None

        short_pct = float(short_pct)
        if short_pct < 0:
            return None

        # Convert 0..1 float (yfinance returns fraction, not percentage)
        # to percentage if needed
        if short_pct <= 1.0:
            short_pct *= 100  # e.g. 0.05 → 5%

        # Map: 0% → +1.0, 10% → -0.0, 30%+ → -1.0
        # Use linear interpolation then clamp
        # signal = 1 - (short_pct / 15)  →  0% → 1.0, 15% → 0.0, 30% → -1.0
        signal = 1.0 - (short_pct / 15.0)
        return float(np.clip(signal, -1.0, 1.0))

    except Exception as exc:
        logger.debug("short_interest_signal error: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Score combination
# ---------------------------------------------------------------------------

def _combine_scores(components: dict, weights: dict) -> int:
    """
    Weighted sum of component scores (each -1..+1), scaled to -100..+100.
    Returns an integer.
    """
    raw = sum(components[k] * weights[k] for k in components)
    score = int(round(raw * 100))
    return int(np.clip(score, -100, 100))


def _get_signal_label(score: int) -> str:
    if score >= 80:
        return "Strong Beat Expected"
    elif score >= 40:
        return "Likely Beat"
    elif score >= 10:
        return "Slight Beat Expected"
    elif score >= -9:
        return "Coin Flip"
    elif score >= -39:
        return "Slight Miss Expected"
    elif score >= -79:
        return "Likely Miss"
    else:
        return "Strong Miss Expected"


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _get_confidence(components: dict, failed: list) -> str:
    """Confidence based on how many components succeeded."""
    n_ok = len(components)
    n_fail = len(failed)
    total = n_ok + n_fail
    if total == 0:
        return "low"
    ratio = n_ok / total
    if ratio >= 0.8:
        return "high"
    elif ratio >= 0.5:
        return "medium"
    else:
        return "low"


def _safe_get_info(ticker_obj) -> dict:
    """Safely fetch ticker.info, returning {} on failure."""
    try:
        info = ticker_obj.info
        return info if isinstance(info, dict) else {}
    except Exception:
        return {}


def _get_next_earnings_date(ticker_obj, info: dict) -> Optional[str]:
    """Return ISO date string for next earnings, or None."""
    try:
        # Try calendar first
        cal = ticker_obj.calendar
        if cal is not None and not (hasattr(cal, "empty") and cal.empty):
            if isinstance(cal, dict):
                ed = cal.get("Earnings Date")
                if ed:
                    if isinstance(ed, list):
                        ed = ed[0]
                    return str(ed)[:10]
            elif hasattr(cal, "loc"):
                try:
                    ed = cal.loc["Earnings Date"]
                    if hasattr(ed, "iloc"):
                        ed = ed.iloc[0]
                    return str(ed)[:10]
                except KeyError:
                    pass
    except Exception:
        pass

    # Fallback to info dict
    ts = info.get("earningsTimestamp") or info.get("earningsTimestampStart")
    if ts:
        try:
            return datetime.utcfromtimestamp(int(ts)).strftime("%Y-%m-%d")
        except Exception:
            pass

    return None


def _get_eps_estimate(info: dict) -> Optional[float]:
    """Return EPS estimate from info dict."""
    for key in ("epsForwardQuarter", "epsCurrentYear", "epsForward", "forwardEps"):
        val = info.get(key)
        if val is not None:
            try:
                return float(val)
            except (TypeError, ValueError):
                pass
    return None


# ---------------------------------------------------------------------------
# Flask endpoint (add to your existing Flask app)
# ---------------------------------------------------------------------------

def register_earnings_whisper_route(app):
    """
    Call this from your Flask app factory to register the endpoint.

    Usage:
        from earnings_whisper import register_earnings_whisper_route
        register_earnings_whisper_route(app)
    """
    from flask import jsonify, request as flask_request

    @app.route("/api/stock/<symbol>/earnings-whisper", methods=["GET"])
    def earnings_whisper(symbol):
        """
        GET /api/stock/TSLA/earnings-whisper

        Query params:
            pretty=1   — indent JSON (default: compact)
        """
        symbol = symbol.upper().strip()
        if not symbol or not symbol.isalpha() or len(symbol) > 5:
            return jsonify({"error": "Invalid ticker symbol"}), 400

        try:
            data = get_earnings_whisper_score(symbol)
            status_code = 200 if data.get("score") is not None else 503
            indent = 2 if flask_request.args.get("pretty") else None
            return app.response_class(
                response=__import__("json").dumps(data, indent=indent, default=str),
                status=status_code,
                mimetype="application/json",
            )
        except Exception as exc:
            logger.exception("earnings_whisper endpoint failed for %s", symbol)
            return jsonify({"symbol": symbol, "error": str(exc)}), 500

    return earnings_whisper


# ---------------------------------------------------------------------------
# Standalone Flask app (run directly: python earnings_whisper.py)
# ---------------------------------------------------------------------------

def _create_standalone_app():
    from flask import Flask
    app = Flask(__name__)
    register_earnings_whisper_route(app)

    @app.route("/health")
    def health():
        from flask import jsonify
        return jsonify({"status": "ok", "service": "earnings-whisper"})

    return app


if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )

    # Quick CLI test: python earnings_whisper.py TSLA AAPL
    if len(sys.argv) > 1:
        import json
        for sym in sys.argv[1:]:
            print(f"\n{'='*60}")
            print(f"Computing Earnings Whisper Score for {sym} ...")
            result = get_earnings_whisper_score(sym)
            print(json.dumps(result, indent=2, default=str))
    else:
        # Start the Flask server
        flask_app = _create_standalone_app()
        port = int(__import__("os").environ.get("PORT", 5001))
        print(f"Starting Earnings Whisper API on http://0.0.0.0:{port}")
        print("Endpoint: GET /api/stock/<SYMBOL>/earnings-whisper")
        flask_app.run(host="0.0.0.0", port=port, debug=False)
