/**
 * Shared test fixtures for Google OAuth + Earnings Whisper tests.
 *
 * Conventions:
 *  - MOCK_GOOGLE_ID_TOKEN  — a syntactically valid (but unsigned) JWT-like
 *    string used wherever the raw Bearer token is needed.
 *  - MOCK_GOOGLE_PAYLOAD   — the decoded payload Google's tokeninfo returns.
 *  - MOCK_YFINANCE_*       — raw Python-dict-style objects mirroring what
 *    yfinance produces so Python unit tests can patch them in.
 *  - MOCK_EARNINGS_RESPONSE — what the Node API returns for a valid symbol.
 */

'use strict';

// ---------------------------------------------------------------------------
// 1. Google OAuth fixtures
// ---------------------------------------------------------------------------

/**
 * A structurally valid HS256 JWT signed with the secret "test-secret".
 * Created with: jwt.encode(MOCK_GOOGLE_PAYLOAD, "test-secret", algorithm="HS256")
 * Do NOT use in production — secret is public.
 */
const MOCK_GOOGLE_ID_TOKEN =
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9' +
  '.eyJpc3MiOiJhY2NvdW50cy5nb29nbGUuY29tIiwiYXpwIjoiNDI0MjQyNDI0Mi1hcHBzLmdvb2dsZXVzZXJjb250ZW50LmNvbSIsImF1ZCI6IjQyNDI0MjQyNDItYXBwcy5nb29nbGV1c2VyY29udGVudC5jb20iLCJzdWIiOiIxMDk4NzY1NDMyMTA5ODc2NTQzMjEiLCJlbWFpbCI6InRlc3R1c2VyQGdtYWlsLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJuYW1lIjoiVGVzdCBVc2VyIiwicGljdHVyZSI6Imh0dHBzOi8vbGgzLmdvb2dsZXVzZXJjb250ZW50LmNvbS9hL3Rlc3QiLCJnaXZlbl9uYW1lIjoiVGVzdCIsImZhbWlseV9uYW1lIjoiVXNlciIsImlhdCI6MTc0NTAwMDAwMCwiZXhwIjo5OTk5OTk5OTk5fQ' +
  '.placeholder-sig-not-verified-in-mocks';

/**
 * Decoded payload — mirrors what google-auth-library / google.oauth2.id_token
 * returns after verify_oauth2_token().
 */
const MOCK_GOOGLE_PAYLOAD = {
  iss: 'accounts.google.com',
  azp: '424242424242-apps.googleusercontent.com',
  aud: '424242424242-apps.googleusercontent.com',
  sub: '109876543210987654321',
  email: 'testuser@gmail.com',
  email_verified: true,
  name: 'Test User',
  picture: 'https://lh3.googleusercontent.com/a/test',
  given_name: 'Test',
  family_name: 'User',
  iat: 1745000000,
  exp: 9999999999, // far future — "never expires" for tests
};

/** Payload for an already-expired token (exp is in the past). */
const MOCK_GOOGLE_PAYLOAD_EXPIRED = {
  ...MOCK_GOOGLE_PAYLOAD,
  iat: 1700000000,
  exp: 1700003600, // expired in 2023
};

/** Second user — used for watchlist isolation tests. */
const MOCK_GOOGLE_PAYLOAD_USER2 = {
  ...MOCK_GOOGLE_PAYLOAD,
  sub: '200000000000000000002',
  email: 'anotheruser@gmail.com',
  name: 'Another User',
};

// ---------------------------------------------------------------------------
// 2. JWT fixtures (app-issued JWTs, separate from Google ID tokens)
// ---------------------------------------------------------------------------

/**
 * A valid app-issued JWT payload (before signing).
 * Your auth route should sign this with process.env.JWT_SECRET.
 */
const MOCK_JWT_PAYLOAD = {
  sub: MOCK_GOOGLE_PAYLOAD.sub,
  email: MOCK_GOOGLE_PAYLOAD.email,
  name: MOCK_GOOGLE_PAYLOAD.name,
  picture: MOCK_GOOGLE_PAYLOAD.picture,
  iat: Math.floor(Date.now() / 1000),
  exp: Math.floor(Date.now() / 1000) + 3600,
};

/** Payload that represents an already-expired app JWT. */
const MOCK_JWT_PAYLOAD_EXPIRED = {
  ...MOCK_JWT_PAYLOAD,
  iat: 1700000000,
  exp: 1700003600,
};

// ---------------------------------------------------------------------------
// 3. yfinance mock data (used by Python unit tests via json.dumps)
// ---------------------------------------------------------------------------

/**
 * Minimal structure that yfinance.Ticker('AAPL').info returns.
 * Only fields consumed by get_earnings_whisper_score() are populated.
 */
const MOCK_YFINANCE_AAPL_INFO = {
  symbol: 'AAPL',
  shortName: 'Apple Inc.',
  trailingEps: 6.57,
  forwardEps: 7.24,
  revenueGrowth: 0.061,
  earningsGrowth: 0.08,
  recommendationMean: 1.9,        // 1=strong buy … 5=strong sell
  numberOfAnalystOpinions: 38,
  earningsQuarterlyGrowth: 0.07,
  shortRatio: 0.88,
  heldPercentInstitutions: 0.6063,
  trailingPE: 28.4,
  forwardPE: 25.8,
  // Dates as Unix timestamps
  mostRecentQuarter: 1735689600,  // 2025-01-01
  nextFiscalYearEnd: 1759276800,  // 2025-09-26
};

/**
 * Minimal calendar object that yfinance.Ticker('AAPL').calendar returns.
 */
const MOCK_YFINANCE_AAPL_CALENDAR = {
  'Earnings Date': ['2025-07-31', '2025-08-04'],
  'Earnings Average': 1.52,
  'Earnings Low': 1.45,
  'Earnings High': 1.62,
  'Revenue Average': 88200000000,
  'Revenue Low': 86100000000,
  'Revenue High': 91900000000,
};

/**
 * yfinance data for an unknown / invalid ticker.
 * yfinance returns an empty info dict when the symbol isn't found.
 */
const MOCK_YFINANCE_INVALID_INFO = {};
const MOCK_YFINANCE_INVALID_CALENDAR = {};

// ---------------------------------------------------------------------------
// 4. Expected API response shapes
// ---------------------------------------------------------------------------

/** Minimum fields the earnings-whisper endpoint must return for a valid symbol. */
const MOCK_EARNINGS_RESPONSE_SHAPE = {
  symbol: expect.any(String),
  score: expect.any(Number),
  factors: expect.objectContaining({
    analyst_revisions: expect.any(Number),
    beat_history: expect.any(Number),
    options_signal: expect.any(Number),
    surprise_size: expect.any(Number),
    short_interest: expect.any(Number),
  }),
  earnings_date: expect.stringMatching(/^\d{4}-\d{2}-\d{2}$/),
  eps_estimate: expect.any(Number),
  eps_previous: expect.any(Number),
  generated_at: expect.any(String),
};

/** User watchlist item shape. */
const MOCK_WATCHLIST_ITEM_SHAPE = {
  symbol: expect.any(String),
  added_at: expect.any(String),
};

// ---------------------------------------------------------------------------
// 5. Watchlist seed data
// ---------------------------------------------------------------------------

const MOCK_WATCHLIST_SYMBOLS = ['AAPL', 'TSLA', 'NVDA'];

// ---------------------------------------------------------------------------
// Exports
// ---------------------------------------------------------------------------

module.exports = {
  MOCK_GOOGLE_ID_TOKEN,
  MOCK_GOOGLE_PAYLOAD,
  MOCK_GOOGLE_PAYLOAD_EXPIRED,
  MOCK_GOOGLE_PAYLOAD_USER2,
  MOCK_JWT_PAYLOAD,
  MOCK_JWT_PAYLOAD_EXPIRED,
  MOCK_YFINANCE_AAPL_INFO,
  MOCK_YFINANCE_AAPL_CALENDAR,
  MOCK_YFINANCE_INVALID_INFO,
  MOCK_YFINANCE_INVALID_CALENDAR,
  MOCK_EARNINGS_RESPONSE_SHAPE,
  MOCK_WATCHLIST_ITEM_SHAPE,
  MOCK_WATCHLIST_SYMBOLS,
};
