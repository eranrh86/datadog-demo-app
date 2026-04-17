const express = require('express');
const axios   = require('axios');
const logger  = require('../utils/logger');
const { asyncHandler } = require('../middleware/errorHandler');
const router  = express.Router();

// ─────────────────────────────────────────────────────────────────────────────
// Social Sentiment — Reddit public JSON API
//
// WHY REDDIT:
//   • Stocktwits API is now gated behind Cloudflare (403 to non-browser clients)
//   • Twitter/X v2 requires a Bearer token ($100/mo on Basic tier for search)
//   • Reddit's public /search.json endpoint is unauthenticated, returns real
//     posts from r/wallstreetbets, r/stocks, r/investing with real usernames,
//     upvote scores, permalinks, and timestamps.
//   • Rate limit: 100 req / 10 min per IP for anonymous clients — plenty for
//     a demo with 5-minute in-process caching.
//
// ENDPOINT:  GET /r/{subreddits}/search.json?q=$SYMBOL&sort=new&limit=10
// AUTH:      none (User-Agent header required to avoid 429)
// ─────────────────────────────────────────────────────────────────────────────

// Simple in-process cache:  symbol → { data, expiresAt }
const SENTIMENT_CACHE     = new Map();
const CACHE_TTL_MS        = 5 * 60 * 1000;   // 5 minutes
const REDDIT_USER_AGENT   = 'KestrelApp/1.0 (stock research terminal; demo)';
const REDDIT_SUBREDDITS   = 'wallstreetbets+stocks+investing';

// Keyword lists for basic NLP sentiment tagging
const BULL_WORDS = [
  'buy', 'bull', 'long', 'call', 'moon', 'bullish', 'bought', 'hold',
  'rocket', 'pump', 'upside', 'breakout', 'accumulate', 'dip', 'green',
  'growth', 'profit', 'gain', 'surge', 'rally', 'beat', 'strong', '🚀', '📈',
];
const BEAR_WORDS = [
  'sell', 'bear', 'short', 'put', 'bearish', 'sold', 'crash', 'dump',
  'overvalued', 'downside', 'drop', 'tank', 'loss', 'cut', 'weak',
  'miss', 'disappointing', 'down', 'decline', 'red', '📉', 'puts',
];

function classifySentiment(text) {
  const lower = text.toLowerCase();
  const bullScore = BULL_WORDS.filter(w => lower.includes(w)).length;
  const bearScore = BEAR_WORDS.filter(w => lower.includes(w)).length;
  if (bullScore === bearScore) return null;   // neutral / unclear
  return bullScore > bearScore ? 'Bullish' : 'Bearish';
}

function timeAgo(utcSeconds) {
  const diffMs  = Date.now() - utcSeconds * 1000;
  const mins    = Math.floor(diffMs / 60_000);
  if (mins < 60)   return `${mins}m ago`;
  const hours   = Math.floor(mins / 60);
  if (hours < 24)  return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

// Mock fallback (same deterministic seed approach as earnings-whisper)
function mockSocialSentiment(symbol) {
  let h = 0;
  for (const c of symbol) h = (Math.imul(31, h) + c.charCodeAt(0)) | 0;
  const seed = Math.abs(h);
  const bull = 35 + (seed % 45);
  return {
    bullPct:  bull,
    bearPct:  100 - bull,
    source:   'mock',
    messages: [
      { user: 'zerohedge_tr',  text: `$${symbol} breakout forming on the daily — volume confirming.`, bull: true,  time_ago: '2h ago', url: `https://reddit.com/r/stocks/search/?q=%24${symbol}` },
      { user: 'markets_arb',   text: `$${symbol} PE premium hard to justify here. Waiting for pullback.`,  bull: false, time_ago: '5h ago', url: `https://reddit.com/r/stocks/search/?q=%24${symbol}` },
      { user: 'optflow_hawk',  text: `Unusual call sweep on $${symbol} — institutional accumulation signal.`, bull: true, time_ago: '1h ago', url: `https://reddit.com/r/stocks/search/?q=%24${symbol}` },
    ],
  };
}

// GET /api/stock/:symbol/social-sentiment
router.get('/:symbol/social-sentiment', asyncHandler(async (req, res) => {
  const symbol = req.params.symbol.toUpperCase().replace(/[^A-Z0-9.]/g, '');

  if (!symbol || symbol.length > 10) {
    return res.status(400).json({ error: 'Invalid ticker symbol' });
  }

  // ── Cache check ──────────────────────────────────────────────────────────
  const cached = SENTIMENT_CACHE.get(symbol);
  if (cached && cached.expiresAt > Date.now()) {
    logger.info('Social sentiment cache hit', { symbol });
    return res.json({ ...cached.data, cached: true });
  }

  logger.info('Social sentiment fetching from Reddit', { symbol });

  try {
    const url = `https://www.reddit.com/r/${REDDIT_SUBREDDITS}/search.json`;
    const resp = await axios.get(url, {
      params: {
        q:           `$${symbol}`,
        sort:        'new',
        limit:       15,
        restrict_sr: 1,
      },
      headers: { 'User-Agent': REDDIT_USER_AGENT },
      timeout: 8000,
    });

    const posts = (resp.data?.data?.children || [])
      .map(c => c.data)
      // Filter out AutoModerator noise
      .filter(p => p.author !== 'AutoModerator' && p.score >= 0);

    if (posts.length === 0) {
      // No posts found — return mock so the widget always has something
      logger.warn('Social sentiment: no Reddit posts found, using mock', { symbol });
      return res.json(mockSocialSentiment(symbol));
    }

    // Build message list with per-post sentiment classification
    const messages = posts.slice(0, 8).map(p => {
      const fullText  = `${p.title} ${p.selftext || ''}`.trim();
      const sentiment = classifySentiment(fullText);
      return {
        user:     p.author,
        text:     p.title.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>'),
        bull:     sentiment !== 'Bearish',          // neutral → treated as bullish
        sentiment: sentiment || 'Neutral',
        score:    p.score,
        comments: p.num_comments,
        subreddit: p.subreddit,
        time_ago:  timeAgo(p.created_utc),
        url:      `https://reddit.com${p.permalink}`,
      };
    });

    // Aggregate bull/bear from classified messages (exclude neutrals from pct math)
    const classified = messages.filter(m => m.sentiment !== 'Neutral');
    const bullCount  = classified.filter(m => m.sentiment === 'Bullish').length;
    const total      = classified.length || 1;
    const bullPct    = Math.round((bullCount / total) * 100);

    const data = {
      bullPct,
      bearPct:  100 - bullPct,
      source:   'reddit',
      post_count: posts.length,
      messages,
    };

    // ── Cache store ──────────────────────────────────────────────────────────
    SENTIMENT_CACHE.set(symbol, { data, expiresAt: Date.now() + CACHE_TTL_MS });

    logger.info('Social sentiment served from Reddit', {
      symbol,
      post_count: posts.length,
      bullPct,
    });

    res.json({ ...data, cached: false });

  } catch (err) {
    logger.error('Social sentiment Reddit fetch failed, using mock', {
      symbol,
      error: err.message,
      status: err.response?.status,
    });
    res.json({ ...mockSocialSentiment(symbol), cached: false });
  }
}));

// ------------------------------------------------------------------
// Deterministic mock data seeded from the symbol string so the same
// symbol always returns a consistent (but varied) score.
// ------------------------------------------------------------------
function symbolSeed(symbol) {
  let h = 0;
  for (let i = 0; i < symbol.length; i++) {
    h = (Math.imul(31, h) + symbol.charCodeAt(i)) | 0;
  }
  return Math.abs(h);
}

function mockEarningsWhisper(symbol) {
  const seed = symbolSeed(symbol);
  const rng = (max, min = 0) => min + (seed % (max - min + 1));

  // Raw score −100 … +100
  const score = ((seed % 201) - 100);

  // Factor contributions (each −30 … +30, sum roughly equals score)
  const factors = {
    analyst_revisions:  ((seed        % 61) - 30),
    beat_history:       (((seed >> 3)  % 61) - 30),
    options_signal:     (((seed >> 6)  % 61) - 30),
    surprise_size:      (((seed >> 9)  % 61) - 30),
    short_interest:     (((seed >> 12) % 61) - 30),
  };

  // Next earnings date: 3 – 45 days from now
  const daysOut = rng(45, 3);
  const earningsDate = new Date();
  earningsDate.setDate(earningsDate.getDate() + daysOut);
  const earningsDateStr = earningsDate.toISOString().split('T')[0];

  // EPS estimate (positive mock)
  const epsEstimate = ((seed % 500) / 100 + 0.10).toFixed(2);
  const epsPrev     = ((seed % 450) / 100 + 0.08).toFixed(2);

  return {
    symbol: symbol.toUpperCase(),
    score,
    factors,
    earnings_date: earningsDateStr,
    eps_estimate:  parseFloat(epsEstimate),
    eps_previous:  parseFloat(epsPrev),
    generated_at:  new Date().toISOString(),
  };
}

// GET /api/stock/:symbol/earnings-whisper
router.get('/:symbol/earnings-whisper', asyncHandler(async (req, res) => {
  const symbol = req.params.symbol.toUpperCase().replace(/[^A-Z0-9.]/g, '');

  if (!symbol || symbol.length > 10) {
    return res.status(400).json({ error: 'Invalid ticker symbol' });
  }

  logger.info('Earnings whisper requested', { symbol });

  // Simulate brief latency (100-350 ms)
  const delay = 100 + (symbolSeed(symbol) % 250);
  await new Promise(r => setTimeout(r, delay));

  const data = mockEarningsWhisper(symbol);

  logger.info('Earnings whisper served', { symbol, score: data.score });

  res.json(data);
}));

module.exports = router;
