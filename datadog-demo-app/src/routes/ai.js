/**
 * StockLens AI Routes
 * Integrates Claude claude-sonnet-4-6 for:
 *  - Feature 1: AI Stock Analyst Chat  (POST /api/stock/:symbol/ai-chat)
 *  - Feature 2: Earnings Whisper Explanation (GET /api/stock/:symbol/earnings-whisper/explain)
 *  - Feature 3: Portfolio Risk Summary  (POST /api/portfolio/ai-summary)
 */

const express = require('express');
const Anthropic = require('@anthropic-ai/sdk');
const logger = require('../utils/logger');
const { asyncHandler } = require('../middleware/errorHandler');

const router = express.Router();

// ---------------------------------------------------------------------------
// Anthropic client — key from env; falls back to hard-coded demo key
// ---------------------------------------------------------------------------
const ANTHROPIC_API_KEY =
  process.env.ANTHROPIC_API_KEY ||
  process.env.ANTHROPIC_API_KEY || '';

const MODEL = 'claude-sonnet-4-6';

function getClient() {
  return new Anthropic({ apiKey: ANTHROPIC_API_KEY });
}

// ---------------------------------------------------------------------------
// Helper: truncate text to word boundary near maxLen
// ---------------------------------------------------------------------------
function truncate(text, maxLen = 1000) {
  if (text.length <= maxLen) return text;
  return text.slice(0, maxLen).replace(/\s+\S*$/, '') + '…';
}

// ===========================================================================
// FEATURE 1 — AI Stock Analyst Chat
// POST /api/stock/:symbol/ai-chat
// Body: { "question": "...", "context": { price, change, marketCap, peRatio } }
// ===========================================================================
router.post('/:symbol/ai-chat', asyncHandler(async (req, res) => {
  const symbol = req.params.symbol.toUpperCase().replace(/[^A-Z0-9.]/g, '');

  if (!symbol || symbol.length > 10) {
    return res.status(400).json({ error: 'Invalid ticker symbol' });
  }

  const { question, context = {} } = req.body;

  if (!question || typeof question !== 'string' || question.trim().length === 0) {
    return res.status(400).json({ error: 'question is required' });
  }

  const { price, change, marketCap, peRatio } = context;

  logger.info('AI stock chat requested', { symbol, question: truncate(question, 120) });

  // Build stock context block
  const stockContext = [
    price     != null ? `Current price: $${price}`              : null,
    change    != null ? `Change today:  ${change}%`             : null,
    marketCap != null ? `Market cap:    ${marketCap}`           : null,
    peRatio   != null ? `P/E ratio:     ${peRatio}`             : null,
  ].filter(Boolean).join('\n');

  const systemPrompt = `You are an expert stock analyst for StockLens, a financial analytics platform.
You are answering questions about ${symbol}.

Current market data for ${symbol}:
${stockContext || 'No live data available — use general knowledge.'}

Instructions:
- Answer in plain English, under 150 words.
- Be factual and balanced; acknowledge uncertainty when relevant.
- Focus on the specific question asked.
- Always end your response with this exact disclaimer on its own line: "Not financial advice."`;

  // Set SSE headers for streaming
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.flushHeaders();

  const citations = [];

  try {
    const client = getClient();
    const stream = client.messages.stream({
      model: MODEL,
      max_tokens: 300,
      system: systemPrompt,
      messages: [{ role: 'user', content: question.trim() }],
    });

    let fullText = '';

    stream.on('text', (text) => {
      fullText += text;
      res.write(`data: ${JSON.stringify({ type: 'delta', text })}\n\n`);
    });

    stream.on('message', () => {
      logger.info('AI stock chat completed', {
        symbol,
        response_length: fullText.length,
      });
      res.write(`data: ${JSON.stringify({ type: 'done', citations })}\n\n`);
      res.end();
    });

    stream.on('error', (err) => {
      logger.error('Claude streaming error', { symbol, error: err.message });
      res.write(`data: ${JSON.stringify({ type: 'error', error: 'AI service unavailable. Please try again.' })}\n\n`);
      res.end();
    });
  } catch (err) {
    logger.error('Claude client error', { symbol, error: err.message });
    res.write(`data: ${JSON.stringify({ type: 'error', error: 'AI service unavailable. Please try again.' })}\n\n`);
    res.end();
  }
}));

// ===========================================================================
// FEATURE 2 — Earnings Whisper Explanation
// GET /api/stock/:symbol/earnings-whisper/explain
// Wraps the existing earnings whisper score with a Claude-generated explanation
// ===========================================================================
router.get('/:symbol/earnings-whisper/explain', asyncHandler(async (req, res) => {
  const symbol = req.params.symbol.toUpperCase().replace(/[^A-Z0-9.]/g, '');

  if (!symbol || symbol.length > 10) {
    return res.status(400).json({ error: 'Invalid ticker symbol' });
  }

  // Accept score_data from query/body, or build a minimal mock
  const scoreData = req.body && Object.keys(req.body).length > 0
    ? req.body
    : buildMockScoreData(symbol);

  logger.info('AI earnings explanation requested', { symbol, score: scoreData.score });

  const { score, factors = {}, earnings_date, eps_estimate, eps_previous } = scoreData;

  const factorLines = Object.entries(factors)
    .map(([k, v]) => `  ${k.replace(/_/g, ' ')}: ${v > 0 ? '+' : ''}${v}`)
    .join('\n');

  const prompt = `You are a financial analyst. Explain the following Earnings Whisper score for ${symbol} in 2-3 plain-English sentences that a retail investor would understand. Be specific about what the score means and which factors are driving it.

Symbol: ${symbol}
Earnings Whisper Score: ${score} (range: -100 bullish … +100 bullish)
Earnings date: ${earnings_date || 'upcoming'}
EPS estimate: $${eps_estimate}  (previous: $${eps_previous})
Factor breakdown (each -30 to +30):
${factorLines || '  (no factor data)'}

Write 2-3 sentences only. Do not use headers or bullet points. End with "Not financial advice."`;

  try {
    const client = getClient();
    const message = await client.messages.create({
      model: MODEL,
      max_tokens: 200,
      messages: [{ role: 'user', content: prompt }],
    });

    const explanation = message.content[0]?.text?.trim() || 'Explanation unavailable.';

    logger.info('AI earnings explanation served', { symbol, explanation_length: explanation.length });

    res.json({
      symbol,
      score,
      explanation,
      score_data: scoreData,
    });
  } catch (err) {
    logger.error('Claude earnings explanation error', { symbol, error: err.message });
    res.json({
      symbol,
      score: scoreData.score,
      explanation: `${symbol} has an earnings whisper score of ${scoreData.score}. Score explanation temporarily unavailable — please try again shortly. Not financial advice.`,
      score_data: scoreData,
      ai_error: true,
    });
  }
}));

// Helper: deterministic mock (mirrors stock.js logic) for standalone testing
function buildMockScoreData(symbol) {
  let h = 0;
  for (let i = 0; i < symbol.length; i++) h = (Math.imul(31, h) + symbol.charCodeAt(i)) | 0;
  const seed = Math.abs(h);
  const score = (seed % 201) - 100;
  const factors = {
    analyst_revisions: ((seed % 61) - 30),
    beat_history:      (((seed >> 3) % 61) - 30),
    options_signal:    (((seed >> 6) % 61) - 30),
    surprise_size:     (((seed >> 9) % 61) - 30),
    short_interest:    (((seed >> 12) % 61) - 30),
  };
  const earningsDate = new Date();
  earningsDate.setDate(earningsDate.getDate() + ((seed % 43) + 3));
  return {
    symbol,
    score,
    factors,
    earnings_date: earningsDate.toISOString().split('T')[0],
    eps_estimate:  parseFloat(((seed % 500) / 100 + 0.10).toFixed(2)),
    eps_previous:  parseFloat(((seed % 450) / 100 + 0.08).toFixed(2)),
  };
}

// ===========================================================================
// FEATURE 3 — Portfolio Risk Summary
// POST /api/portfolio/ai-summary
// Body: { holdings: [{ symbol, shares, avg_cost, current_price }] }
// ===========================================================================
router.post('/portfolio/ai-summary', asyncHandler(async (req, res) => {
  const { holdings } = req.body;

  if (!Array.isArray(holdings) || holdings.length === 0) {
    return res.status(400).json({ error: 'holdings array is required and must not be empty' });
  }

  // Validate and sanitize
  const sanitized = holdings
    .filter(h => h && typeof h.symbol === 'string')
    .map(h => ({
      symbol:        h.symbol.toUpperCase().replace(/[^A-Z0-9.]/g, '').slice(0, 10),
      shares:        parseFloat(h.shares)       || 0,
      avg_cost:      parseFloat(h.avg_cost)     || 0,
      current_price: parseFloat(h.current_price) || 0,
    }))
    .filter(h => h.symbol && h.shares > 0);

  if (sanitized.length === 0) {
    return res.status(400).json({ error: 'No valid holdings found' });
  }

  logger.info('AI portfolio summary requested', { holding_count: sanitized.length });

  // Build portfolio summary table
  let totalValue = 0;
  const holdingLines = sanitized.map(h => {
    const positionValue = h.shares * (h.current_price || h.avg_cost);
    const gainLoss = h.current_price
      ? (((h.current_price - h.avg_cost) / h.avg_cost) * 100).toFixed(1)
      : 'N/A';
    totalValue += positionValue;
    return `  ${h.symbol}: ${h.shares} shares @ $${h.avg_cost} avg cost, current $${h.current_price || 'N/A'}, P&L: ${gainLoss}%`;
  }).join('\n');

  const prompt = `You are a portfolio risk analyst. Analyze this portfolio and respond with EXACTLY 3 bullet points (using • as the bullet character). Each bullet should cover a different risk dimension: concentration risk, market/sector exposure, and one specific actionable insight. Keep each bullet to 1-2 sentences. End the last bullet with "Not financial advice."

Portfolio (total value: ~$${totalValue.toFixed(0)}):
${holdingLines}

Respond only with the 3 bullet points, nothing else.`;

  try {
    const client = getClient();
    const message = await client.messages.create({
      model: MODEL,
      max_tokens: 300,
      messages: [{ role: 'user', content: prompt }],
    });

    const rawSummary = message.content[0]?.text?.trim() || '';

    // Parse bullet points into an array
    const bullets = rawSummary
      .split('\n')
      .map(l => l.replace(/^[•\-*]\s*/, '').trim())
      .filter(l => l.length > 0)
      .slice(0, 3);

    logger.info('AI portfolio summary served', { holding_count: sanitized.length });

    res.json({
      summary: bullets,
      raw: rawSummary,
      total_value: parseFloat(totalValue.toFixed(2)),
      holding_count: sanitized.length,
    });
  } catch (err) {
    logger.error('Claude portfolio summary error', { error: err.message });
    res.json({
      summary: [
        `Your portfolio holds ${sanitized.length} positions with a combined value of ~$${totalValue.toFixed(0)}.`,
        'Risk assessment temporarily unavailable — please try again shortly.',
        'Diversification and position sizing review recommended. Not financial advice.',
      ],
      ai_error: true,
      total_value: parseFloat(totalValue.toFixed(2)),
      holding_count: sanitized.length,
    });
  }
}));

module.exports = router;
