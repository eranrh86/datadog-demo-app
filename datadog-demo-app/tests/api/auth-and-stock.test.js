/**
 * API integration tests for:
 *   POST /auth/google           — Google OAuth exchange
 *   GET  /api/user/watchlist    — authenticated watchlist
 *   GET  /api/stock/:sym/earnings-whisper — earnings whisper score
 *
 * Uses supertest so no real HTTP server is needed.
 * Google token verification is mocked so no real Google account is required.
 */

'use strict';

const request = require('supertest');
const app = require('../../src/app');

const {
  MOCK_GOOGLE_ID_TOKEN,
  MOCK_GOOGLE_PAYLOAD,
  MOCK_EARNINGS_RESPONSE_SHAPE,
  MOCK_WATCHLIST_SYMBOLS,
} = require('../fixtures/mock-data');

// ── Helpers ───────────────────────────────────────────────────────────────

/**
 * Returns a signed app JWT for use in Authorization headers.
 * If /auth/google exists it calls it; otherwise fabricates one locally
 * so the watchlist tests can run even before the auth route is built.
 */
async function getValidAppJwt() {
  try {
    const res = await request(app)
      .post('/auth/google')
      .send({ id_token: MOCK_GOOGLE_ID_TOKEN });
    if (res.status === 200 && res.body.token) return res.body.token;
  } catch (_) { /* route not yet implemented */ }

  // Fallback: fabricate a minimal JWT for route tests
  const crypto = require('crypto');
  const secret = process.env.JWT_SECRET || 'test-jwt-secret-not-for-production';
  const payload = {
    sub: MOCK_GOOGLE_PAYLOAD.sub,
    email: MOCK_GOOGLE_PAYLOAD.email,
    name: MOCK_GOOGLE_PAYLOAD.name,
    iat: Math.floor(Date.now() / 1000),
    exp: Math.floor(Date.now() / 1000) + 3600,
  };
  function b64url(obj) {
    return Buffer.from(JSON.stringify(obj))
      .toString('base64').replace(/=/g,'').replace(/\+/g,'-').replace(/\//g,'_');
  }
  const h = b64url({ alg: 'HS256', typ: 'JWT' });
  const b = b64url(payload);
  const sig = crypto.createHmac('sha256', secret)
    .update(`${h}.${b}`).digest('base64')
    .replace(/=/g,'').replace(/\+/g,'-').replace(/\//g,'_');
  return `${h}.${b}.${sig}`;
}

// ── POST /auth/google ─────────────────────────────────────────────────────

describe('POST /auth/google', () => {
  // NOTE: if this route doesn't exist yet, tests are marked pending (xtest)
  // so they don't fail CI — swap xtest → test once the route is implemented.

  xtest('returns 200 + JWT on valid Google ID token', async () => {
    const res = await request(app)
      .post('/auth/google')
      .send({ id_token: MOCK_GOOGLE_ID_TOKEN })
      .expect(200);

    expect(res.body).toHaveProperty('token');
    expect(typeof res.body.token).toBe('string');
    expect(res.body.token.split('.')).toHaveLength(3); // JWT structure
  });

  xtest('returned JWT payload contains user email and name', async () => {
    const res = await request(app)
      .post('/auth/google')
      .send({ id_token: MOCK_GOOGLE_ID_TOKEN })
      .expect(200);

    const [, bodyB64] = res.body.token.split('.');
    const payload = JSON.parse(Buffer.from(bodyB64, 'base64url').toString('utf8'));
    expect(payload.email).toBe(MOCK_GOOGLE_PAYLOAD.email);
    expect(payload.name).toBe(MOCK_GOOGLE_PAYLOAD.name);
  });

  xtest('returns 401 for invalid / tampered Google ID token', async () => {
    const res = await request(app)
      .post('/auth/google')
      .send({ id_token: 'tampered.google.token' })
      .expect(401);

    expect(res.body).toHaveProperty('error');
  });

  xtest('returns 400 when id_token field is missing from body', async () => {
    const res = await request(app)
      .post('/auth/google')
      .send({})
      .expect(400);

    expect(res.body).toHaveProperty('error');
  });

  xtest('returns 401 for expired Google ID token', async () => {
    // An expired token should be rejected even if structurally valid.
    const expiredToken = [
      'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9',
      Buffer.from(JSON.stringify({
        iss: 'accounts.google.com',
        aud: process.env.GOOGLE_CLIENT_ID || 'test-client-id',
        sub: '12345',
        email: 'test@gmail.com',
        email_verified: true,
        exp: 1700003600, // expired
        iat: 1700000000,
      })).toString('base64url'),
      'invalidsignature',
    ].join('.');

    const res = await request(app)
      .post('/auth/google')
      .send({ id_token: expiredToken })
      .expect(401);

    expect(res.body).toHaveProperty('error');
  });
});

// ── GET /api/user/watchlist ───────────────────────────────────────────────

describe('GET /api/user/watchlist', () => {
  xtest('returns 401 when no Authorization header is present', async () => {
    const res = await request(app)
      .get('/api/user/watchlist')
      .expect(401);

    expect(res.body).toHaveProperty('error');
  });

  xtest('returns 401 for malformed Bearer token', async () => {
    const res = await request(app)
      .get('/api/user/watchlist')
      .set('Authorization', 'Bearer not-a-real-jwt')
      .expect(401);

    expect(res.body).toHaveProperty('error');
  });

  xtest('returns 401 for expired app JWT', async () => {
    const expiredJwt = await (async () => {
      const crypto = require('crypto');
      const secret = process.env.JWT_SECRET || 'test-jwt-secret-not-for-production';
      function b64url(obj) {
        return Buffer.from(JSON.stringify(obj))
          .toString('base64').replace(/=/g,'').replace(/\+/g,'-').replace(/\//g,'_');
      }
      const h = b64url({ alg: 'HS256', typ: 'JWT' });
      const b = b64url({ sub: '123', email: 'x@x.com', iat: 1700000000, exp: 1700003600 });
      const sig = crypto.createHmac('sha256', secret)
        .update(`${h}.${b}`).digest('base64')
        .replace(/=/g,'').replace(/\+/g,'-').replace(/\//g,'_');
      return `${h}.${b}.${sig}`;
    })();

    const res = await request(app)
      .get('/api/user/watchlist')
      .set('Authorization', `Bearer ${expiredJwt}`)
      .expect(401);

    expect(res.body).toHaveProperty('error');
  });

  xtest('returns 200 + array for valid JWT', async () => {
    const token = await getValidAppJwt();
    const res = await request(app)
      .get('/api/user/watchlist')
      .set('Authorization', `Bearer ${token}`)
      .expect(200);

    expect(Array.isArray(res.body)).toBe(true);
  });

  xtest('returns 200 + empty array for brand-new user with no watchlist', async () => {
    const token = await getValidAppJwt();
    const res = await request(app)
      .get('/api/user/watchlist')
      .set('Authorization', `Bearer ${token}`)
      .expect(200);

    // Fresh test DB — should be empty
    expect(res.body).toEqual([]);
  });

  xtest('watchlist items contain symbol and added_at fields', async () => {
    const token = await getValidAppJwt();

    // Add a symbol first
    await request(app)
      .post('/api/user/watchlist')
      .set('Authorization', `Bearer ${token}`)
      .send({ symbol: 'AAPL' });

    const res = await request(app)
      .get('/api/user/watchlist')
      .set('Authorization', `Bearer ${token}`)
      .expect(200);

    expect(res.body.length).toBeGreaterThan(0);
    expect(res.body[0]).toHaveProperty('symbol');
    expect(res.body[0]).toHaveProperty('added_at');
  });
});

// ── GET /api/stock/:symbol/earnings-whisper ───────────────────────────────
// These use the REAL route (already implemented) — no xtest.

describe('GET /api/stock/:symbol/earnings-whisper', () => {
  test('returns 200 for AAPL with all required fields', async () => {
    const res = await request(app)
      .get('/api/stock/AAPL/earnings-whisper')
      .expect(200);

    expect(res.body).toMatchObject({
      symbol: expect.any(String),
      score: expect.any(Number),
      factors: expect.any(Object),
      earnings_date: expect.stringMatching(/^\d{4}-\d{2}-\d{2}$/),
      eps_estimate: expect.any(Number),
      eps_previous: expect.any(Number),
      generated_at: expect.any(String),
    });
  });

  test('score for AAPL is within [-100, +100]', async () => {
    const res = await request(app)
      .get('/api/stock/AAPL/earnings-whisper')
      .expect(200);

    expect(res.body.score).toBeGreaterThanOrEqual(-100);
    expect(res.body.score).toBeLessThanOrEqual(100);
  });

  test('score for TSLA is within [-100, +100]', async () => {
    const res = await request(app)
      .get('/api/stock/TSLA/earnings-whisper')
      .expect(200);

    expect(res.body.score).toBeGreaterThanOrEqual(-100);
    expect(res.body.score).toBeLessThanOrEqual(100);
  });

  test('score for NVDA is within [-100, +100]', async () => {
    const res = await request(app)
      .get('/api/stock/NVDA/earnings-whisper')
      .expect(200);

    expect(res.body.score).toBeGreaterThanOrEqual(-100);
    expect(res.body.score).toBeLessThanOrEqual(100);
  });

  test('returns 400 for symbol longer than 10 characters', async () => {
    const res = await request(app)
      .get('/api/stock/TOOLONGSYMBOL123/earnings-whisper')
      .expect(400);

    expect(res.body).toHaveProperty('error');
    expect(typeof res.body.error).toBe('string');
  });

  test('all five factor keys are present in response', async () => {
    const res = await request(app)
      .get('/api/stock/MSFT/earnings-whisper')
      .expect(200);

    const { factors } = res.body;
    ['analyst_revisions', 'beat_history', 'options_signal', 'surprise_size', 'short_interest']
      .forEach(key => expect(factors).toHaveProperty(key));
  });

  test('two consecutive calls for the same symbol return identical scores', async () => {
    const [r1, r2] = await Promise.all([
      request(app).get('/api/stock/GOOGL/earnings-whisper'),
      request(app).get('/api/stock/GOOGL/earnings-whisper'),
    ]);
    expect(r1.body.score).toBe(r2.body.score);
  });

  test('different symbols produce different scores', async () => {
    const [r1, r2] = await Promise.all([
      request(app).get('/api/stock/AAPL/earnings-whisper'),
      request(app).get('/api/stock/AMZN/earnings-whisper'),
    ]);
    // AAPL and AMZN should hash to different scores (very high confidence)
    expect(r1.body.score).not.toBe(r2.body.score);
  });

  test('symbol in response is uppercased regardless of input case', async () => {
    const res = await request(app)
      .get('/api/stock/nvda/earnings-whisper')
      .expect(200);
    expect(res.body.symbol).toBe('NVDA');
  });

  test('response content-type is application/json', async () => {
    await request(app)
      .get('/api/stock/AAPL/earnings-whisper')
      .expect('Content-Type', /application\/json/);
  });

  test('eps_estimate and eps_previous are positive numbers', async () => {
    const res = await request(app)
      .get('/api/stock/AAPL/earnings-whisper')
      .expect(200);

    expect(res.body.eps_estimate).toBeGreaterThan(0);
    expect(res.body.eps_previous).toBeGreaterThan(0);
  });

  test('earnings_date is a valid future date', async () => {
    const res = await request(app)
      .get('/api/stock/AAPL/earnings-whisper')
      .expect(200);

    const parsed = new Date(res.body.earnings_date);
    expect(parsed.getTime()).not.toBeNaN();
    // Allow 1 day buffer for timezone differences
    expect(parsed.getTime()).toBeGreaterThan(Date.now() - 86400000);
  });

  // ── Batch of symbols to validate range coverage ──────────────────────

  const BATCH_SYMBOLS = ['AAPL', 'TSLA', 'NVDA', 'MSFT', 'AMZN', 'META', 'GOOGL', 'A', 'BRK.B'];

  test.each(BATCH_SYMBOLS)(
    'score for %s is always in [-100, +100]',
    async (symbol) => {
      const res = await request(app)
        .get(`/api/stock/${symbol}/earnings-whisper`)
        .expect(200);
      expect(res.body.score).toBeGreaterThanOrEqual(-100);
      expect(res.body.score).toBeLessThanOrEqual(100);
    }
  );
});

// ── Cross-feature: auth + stock ───────────────────────────────────────────

describe('Authenticated stock requests', () => {
  xtest('authenticated user can fetch earnings whisper (JWT in header)', async () => {
    const token = await getValidAppJwt();
    const res = await request(app)
      .get('/api/stock/AAPL/earnings-whisper')
      .set('Authorization', `Bearer ${token}`)
      .expect(200);

    expect(res.body.score).toBeGreaterThanOrEqual(-100);
    expect(res.body.score).toBeLessThanOrEqual(100);
  });
});
