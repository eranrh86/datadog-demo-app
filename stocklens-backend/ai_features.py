"""
StockLens AI Features — Python / Flask implementation
Uses Anthropic's Python SDK with claude-sonnet-4-6.

Install dependencies:
    pip install flask anthropic

Environment variable (optional — falls back to demo key):
    export ANTHROPIC_API_KEY=""

Run standalone:
    python ai_features.py
"""

import os
import json
import logging
from typing import Any

import anthropic
from flask import Flask, request, jsonify, Response, stream_with_context

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
ANTHROPIC_API_KEY = os.environ.get(
    "ANTHROPIC_API_KEY",
    "",
)
MODEL = "claude-sonnet-4-6"
MAX_CHAT_TOKENS = 300
MAX_EXPLANATION_TOKENS = 200
MAX_SUMMARY_TOKENS = 300

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

app = Flask(__name__)


def _client() -> anthropic.Anthropic:
    """Return a configured Anthropic client."""
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


# ===========================================================================
# FEATURE 1 — AI Stock Analyst Chat
# POST /api/stock/<symbol>/ai-chat
# Body: { "question": "...", "context": { price, change, marketCap, peRatio } }
# Returns: streaming SSE  (text/event-stream)  OR  { "answer": "...", "citations": [] }
# ===========================================================================
@app.route("/api/stock/<symbol>/ai-chat", methods=["POST"])
def ai_stock_chat(symbol: str):
    symbol = symbol.upper()[:10]
    if not symbol.replace(".", "").isalnum():
        return jsonify({"error": "Invalid ticker symbol"}), 400

    body = request.get_json(silent=True) or {}
    question: str = (body.get("question") or "").strip()
    if not question:
        return jsonify({"error": "question is required"}), 400

    ctx: dict = body.get("context") or {}
    price      = ctx.get("price")
    change     = ctx.get("change")
    market_cap = ctx.get("marketCap")
    pe_ratio   = ctx.get("peRatio")

    stock_lines = "\n".join(filter(None, [
        f"Current price: ${price}"      if price      is not None else None,
        f"Change today:  {change}%"     if change     is not None else None,
        f"Market cap:    {market_cap}"  if market_cap is not None else None,
        f"P/E ratio:     {pe_ratio}"    if pe_ratio   is not None else None,
    ])) or "No live data available — use general knowledge."

    system_prompt = (
        f"You are an expert stock analyst for StockLens, a financial analytics platform.\n"
        f"You are answering questions about {symbol}.\n\n"
        f"Current market data for {symbol}:\n{stock_lines}\n\n"
        f"Instructions:\n"
        f"- Answer in plain English, under 150 words.\n"
        f"- Be factual and balanced; acknowledge uncertainty when relevant.\n"
        f"- Focus on the specific question asked.\n"
        f"- Always end your response with this exact disclaimer on its own line: \"Not financial advice.\""
    )

    log.info("AI stock chat requested symbol=%s question=%.80s", symbol, question)

    # ---- Streaming SSE response ----
    def generate():
        citations: list = []
        try:
            client = _client()
            with client.messages.stream(
                model=MODEL,
                max_tokens=MAX_CHAT_TOKENS,
                system=system_prompt,
                messages=[{"role": "user", "content": question}],
            ) as stream:
                for text in stream.text_stream:
                    yield f"data: {json.dumps({'type': 'delta', 'text': text})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'citations': citations})}\n\n"
        except anthropic.APIError as exc:
            log.error("Claude API error symbol=%s error=%s", symbol, exc)
            yield f"data: {json.dumps({'type': 'error', 'error': 'AI service unavailable. Please try again.'})}\n\n"

    return Response(
        stream_with_context(generate()),
        content_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ===========================================================================
# FEATURE 2 — Earnings Whisper Explanation (utility function + route)
# ===========================================================================
def get_earnings_explanation(symbol: str, score_data: dict) -> str:
    """
    Call Claude to explain the Earnings Whisper score in 2-3 plain-English sentences.

    Args:
        symbol:     Ticker symbol, e.g. "AAPL"
        score_data: Dict with keys: score, factors, earnings_date,
                    eps_estimate, eps_previous  (as returned by the EW API)

    Returns:
        A 2-3 sentence plain-English string ending with "Not financial advice."
        Falls back to a template string if Claude is unavailable.

    Example output:
        "AAPL has beaten earnings 7 of the last 8 quarters, and analysts have been
        raising their estimates ahead of this report. The options market is pricing
        in a smaller move than usual, which combined with the strong beat history
        gives a bullish whisper score of +67. Not financial advice."
    """
    score:         int   = score_data.get("score", 0)
    factors:       dict  = score_data.get("factors") or {}
    earnings_date: str   = score_data.get("earnings_date", "upcoming")
    eps_estimate:  float = score_data.get("eps_estimate", 0)
    eps_previous:  float = score_data.get("eps_previous", 0)

    factor_text = "\n".join(
        f"  {k.replace('_', ' ')}: {'+' if v >= 0 else ''}{v}"
        for k, v in factors.items()
    ) or "  (no factor data)"

    prompt = (
        f"You are a financial analyst. Explain the following Earnings Whisper score for "
        f"{symbol} in 2-3 plain-English sentences that a retail investor would understand. "
        f"Be specific about what the score means and which factors are driving it.\n\n"
        f"Symbol: {symbol}\n"
        f"Earnings Whisper Score: {score} (range: -100 bearish … +100 bullish)\n"
        f"Earnings date: {earnings_date}\n"
        f"EPS estimate: ${eps_estimate}  (previous: ${eps_previous})\n"
        f"Factor breakdown (each -30 to +30):\n{factor_text}\n\n"
        f"Write 2-3 sentences only. Do not use headers or bullet points. "
        f'End with "Not financial advice."'
    )

    try:
        client = _client()
        message = client.messages.create(
            model=MODEL,
            max_tokens=MAX_EXPLANATION_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        explanation = (message.content[0].text or "").strip()
        log.info("Earnings explanation generated symbol=%s score=%d", symbol, score)
        return explanation
    except anthropic.APIError as exc:
        log.error("Claude earnings explanation error symbol=%s error=%s", symbol, exc)
        direction = "bullish" if score > 0 else "bearish" if score < 0 else "neutral"
        return (
            f"{symbol} has an earnings whisper score of {score:+d}, "
            f"which is considered {direction}. "
            f"Key drivers include analyst estimate revisions and historical beat rate. "
            f"Not financial advice."
        )


@app.route("/api/stock/<symbol>/earnings-whisper/explain", methods=["GET", "POST"])
def earnings_whisper_explain(symbol: str):
    symbol = symbol.upper()[:10]
    if not symbol.replace(".", "").isalnum():
        return jsonify({"error": "Invalid ticker symbol"}), 400

    score_data: dict = request.get_json(silent=True) or {}
    if not score_data:
        # Build deterministic mock (mirrors JS logic)
        score_data = _mock_score_data(symbol)

    explanation = get_earnings_explanation(symbol, score_data)

    return jsonify({
        "symbol":      symbol,
        "score":       score_data.get("score"),
        "explanation": explanation,
        "score_data":  score_data,
    })


# ===========================================================================
# FEATURE 3 — Portfolio Risk Summary (utility function + route)
# POST /api/portfolio/ai-summary
# Body: { holdings: [{ symbol, shares, avg_cost, current_price }] }
# ===========================================================================
def get_portfolio_ai_summary(holdings: list[dict[str, Any]]) -> str:
    """
    Given a list of portfolio holdings, ask Claude to summarize the risk as
    3 bullet points covering: concentration, sector/market exposure, and
    one actionable insight.

    Args:
        holdings: List of dicts with keys:
                  symbol (str), shares (float), avg_cost (float),
                  current_price (float, optional)

    Returns:
        A string with 3 bullet points (• prefix), newline-separated.
        Falls back to a template string if Claude is unavailable.
    """
    if not holdings:
        raise ValueError("holdings list must not be empty")

    total_value = 0.0
    holding_lines: list[str] = []

    for h in holdings:
        sym   = str(h.get("symbol", "?")).upper()[:10]
        shrs  = float(h.get("shares", 0) or 0)
        cost  = float(h.get("avg_cost", 0) or 0)
        price = float(h.get("current_price", 0) or 0)

        pos_value = shrs * (price if price else cost)
        total_value += pos_value

        if price and cost:
            pnl = f"{((price - cost) / cost * 100):.1f}%"
        else:
            pnl = "N/A"

        holding_lines.append(
            f"  {sym}: {shrs} shares @ ${cost:.2f} avg cost, "
            f"current ${price:.2f}, P&L: {pnl}"
        )

    prompt = (
        "You are a portfolio risk analyst. Analyze this portfolio and respond with "
        "EXACTLY 3 bullet points (using • as the bullet character). Each bullet should "
        "cover a different risk dimension: (1) concentration risk, (2) market/sector "
        "exposure, (3) one specific actionable insight. Keep each bullet to 1-2 sentences. "
        'End the last bullet with "Not financial advice."\n\n'
        f"Portfolio (total value: ~${total_value:,.0f}):\n"
        + "\n".join(holding_lines)
        + "\n\nRespond only with the 3 bullet points, nothing else."
    )

    try:
        client = _client()
        message = client.messages.create(
            model=MODEL,
            max_tokens=MAX_SUMMARY_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = (message.content[0].text or "").strip()
        log.info("Portfolio summary generated holdings=%d", len(holdings))
        return raw
    except anthropic.APIError as exc:
        log.error("Claude portfolio summary error error=%s", exc)
        symbols = ", ".join(
            str(h.get("symbol", "?")).upper() for h in holdings[:5]
        )
        suffix = "..." if len(holdings) > 5 else ""
        return (
            f"• Your portfolio holds {len(holdings)} positions ({symbols}{suffix}) "
            f"with a combined value of ~${total_value:,.0f}.\n"
            f"• Risk assessment is temporarily unavailable — please try again shortly.\n"
            f"• Consider reviewing position sizing and sector concentration regularly. "
            f"Not financial advice."
        )


@app.route("/api/portfolio/ai-summary", methods=["POST"])
def portfolio_ai_summary():
    body = request.get_json(silent=True) or {}
    holdings: list = body.get("holdings") or []

    if not isinstance(holdings, list) or not holdings:
        return jsonify({"error": "holdings array is required and must not be empty"}), 400

    # Sanitize
    clean = [
        h for h in holdings
        if isinstance(h, dict) and h.get("symbol") and float(h.get("shares", 0) or 0) > 0
    ]
    if not clean:
        return jsonify({"error": "No valid holdings found"}), 400

    raw_summary = get_portfolio_ai_summary(clean)

    # Parse bullets into a list
    bullets = [
        line.lstrip("•-* ").strip()
        for line in raw_summary.splitlines()
        if line.strip()
    ][:3]

    total_value = sum(
        float(h.get("shares", 0) or 0) * float(h.get("current_price") or h.get("avg_cost", 0) or 0)
        for h in clean
    )

    return jsonify({
        "summary":       bullets,
        "raw":           raw_summary,
        "total_value":   round(total_value, 2),
        "holding_count": len(clean),
    })


# ===========================================================================
# Helpers
# ===========================================================================
def _mock_score_data(symbol: str) -> dict:
    """Deterministic mock score (mirrors the JS symbolSeed logic)."""
    h = 0
    for ch in symbol:
        h = ((31 * h) + ord(ch)) & 0xFFFFFFFF
    seed = h
    score = (seed % 201) - 100

    from datetime import date, timedelta
    earnings_date = (date.today() + timedelta(days=((seed % 43) + 3))).isoformat()

    return {
        "symbol":        symbol,
        "score":         score,
        "factors": {
            "analyst_revisions": ((seed        % 61) - 30),
            "beat_history":      (((seed >> 3)  % 61) - 30),
            "options_signal":    (((seed >> 6)  % 61) - 30),
            "surprise_size":     (((seed >> 9)  % 61) - 30),
            "short_interest":    (((seed >> 12) % 61) - 30),
        },
        "earnings_date": earnings_date,
        "eps_estimate":  round((seed % 500) / 100 + 0.10, 2),
        "eps_previous":  round((seed % 450) / 100 + 0.08, 2),
    }


# ===========================================================================
# Run
# ===========================================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    log.info("StockLens AI features starting on port %d  model=%s", port, MODEL)
    app.run(host="0.0.0.0", port=port, debug=False)
