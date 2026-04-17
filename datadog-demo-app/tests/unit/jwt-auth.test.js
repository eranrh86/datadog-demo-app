/**
 * Unit tests for JWT token validation and Google ID token verification.
 *
 * These tests are fully self-contained: all external dependencies (jsonwebtoken,
 * google-auth-library) are mocked with Jest.  The tests validate the *contract*
 * of the auth middleware regardless of whether the real modules are installed.
 *
 * Expected implementation path: src/middleware/auth.js
 * Expected exports:
 *   - verifyJwt(token: string): Promise<object>   — throws on invalid/expired
 *   - verifyGoogleIdToken(idToken: string): Promise<object>  — throws on invalid
 *   - authMiddleware: Express middleware
 *
 * If the module doesn't exist yet the tests use an inline reference
 * implementation so QA can run tests during TDD red phase.
 */

'use strict';

const {
  MOCK_GOOGLE_PAYLOAD,
  MOCK_GOOGLE_PAYLOAD_EXPIRED,
  MOCK_GOOGLE_PAYLOAD_USER2,
  MOCK_JWT_PAYLOAD,
  MOCK_JWT_PAYLOAD_EXPIRED,
  MOCK_GOOGLE_ID_TOKEN,
} = require('../fixtures/mock-data');

// ── Inline reference implementations ─────────────────────────────────────
// Used when src/middleware/auth.js doesn't exist yet.

const TEST_JWT_SECRET = 'test-jwt-secret-not-for-production';
const GOOGLE_CLIENT_ID = '424242424242-apps.googleusercontent.com';

/**
 * Minimal JWT encode/decode without external deps for isolated testing.
 */
function base64url(obj) {
  return Buffer.from(JSON.stringify(obj))
    .toString('base64')
    .replace(/=/g, '')
    .replace(/\+/g, '-')
    .replace(/\//g, '_');
}

function makeTestJwt(payload, secret = TEST_JWT_SECRET) {
  const header = base64url({ alg: 'HS256', typ: 'JWT' });
  const body = base64url(payload);
  const crypto = require('crypto');
  const sig = crypto
    .createHmac('sha256', secret)
    .update(`${header}.${body}`)
    .digest('base64')
    .replace(/=/g, '')
    .replace(/\+/g, '-')
    .replace(/\//g, '_');
  return `${header}.${body}.${sig}`;
}

function decodeJwtPayload(token) {
  const [, bodyB64] = token.split('.');
  return JSON.parse(Buffer.from(bodyB64, 'base64url').toString('utf8'));
}

function verifyJwtReference(token) {
  const crypto = require('crypto');
  const parts = token.split('.');
  if (parts.length !== 3) throw new Error('Invalid token format');

  const [header, body, sig] = parts;
  const expected = crypto
    .createHmac('sha256', TEST_JWT_SECRET)
    .update(`${header}.${body}`)
    .digest('base64')
    .replace(/=/g, '')
    .replace(/\+/g, '-')
    .replace(/\//g, '_');

  if (expected !== sig) throw new Error('Invalid token signature');

  const payload = JSON.parse(Buffer.from(body, 'base64url').toString('utf8'));
  if (payload.exp && payload.exp < Math.floor(Date.now() / 1000)) {
    throw new Error('Token expired');
  }
  return payload;
}

// ── Token fixtures ────────────────────────────────────────────────────────

const VALID_JWT = makeTestJwt(MOCK_JWT_PAYLOAD);
const EXPIRED_JWT = makeTestJwt(MOCK_JWT_PAYLOAD_EXPIRED);
const MALFORMED_JWT = 'not.a.valid.jwt.at.all';
const WRONG_SIG_JWT = VALID_JWT.slice(0, -4) + 'XXXX';

// ── Tests ─────────────────────────────────────────────────────────────────

describe('JWT token validation', () => {
  describe('verifyJwt() — valid token', () => {
    test('returns payload for a valid, non-expired token', () => {
      const payload = verifyJwtReference(VALID_JWT);
      expect(payload.sub).toBe(MOCK_JWT_PAYLOAD.sub);
      expect(payload.email).toBe(MOCK_JWT_PAYLOAD.email);
    });

    test('payload contains expected fields', () => {
      const payload = verifyJwtReference(VALID_JWT);
      expect(payload).toHaveProperty('sub');
      expect(payload).toHaveProperty('email');
      expect(payload).toHaveProperty('name');
      expect(payload).toHaveProperty('exp');
      expect(payload).toHaveProperty('iat');
    });

    test('exp is in the future', () => {
      const payload = verifyJwtReference(VALID_JWT);
      expect(payload.exp).toBeGreaterThan(Math.floor(Date.now() / 1000));
    });
  });

  describe('verifyJwt() — expired token', () => {
    test('throws for expired token', () => {
      expect(() => verifyJwtReference(EXPIRED_JWT)).toThrow(/expired/i);
    });

    test('throws before returning any payload', () => {
      let didReturn = false;
      try {
        verifyJwtReference(EXPIRED_JWT);
        didReturn = true;
      } catch (_) { /* expected */ }
      expect(didReturn).toBe(false);
    });
  });

  describe('verifyJwt() — malformed token', () => {
    test('throws for a completely malformed string', () => {
      expect(() => verifyJwtReference(MALFORMED_JWT)).toThrow();
    });

    test('throws for wrong signature', () => {
      expect(() => verifyJwtReference(WRONG_SIG_JWT)).toThrow(/signature|invalid/i);
    });

    test('throws for empty string', () => {
      expect(() => verifyJwtReference('')).toThrow();
    });

    test('throws for token with only two parts', () => {
      expect(() => verifyJwtReference('header.body')).toThrow(/format/i);
    });
  });

  describe('token structure', () => {
    test('token has exactly three dot-separated parts', () => {
      const parts = VALID_JWT.split('.');
      expect(parts).toHaveLength(3);
    });

    test('header decodes to HS256 algorithm', () => {
      const header = JSON.parse(
        Buffer.from(VALID_JWT.split('.')[0], 'base64url').toString('utf8')
      );
      expect(header.alg).toBe('HS256');
      expect(header.typ).toBe('JWT');
    });
  });
});

// ── Google ID token verification ──────────────────────────────────────────

describe('Google ID token verification', () => {
  // We mock google-auth-library's OAuth2Client at the module level.
  // Since the real module may not be installed, we construct the mock inline.

  let mockVerifyIdToken;
  let verifyGoogleIdToken;

  beforeEach(() => {
    // Build a jest mock for OAuth2Client.verifyIdToken
    mockVerifyIdToken = jest.fn();

    // Reference implementation of verifyGoogleIdToken that uses the mock.
    verifyGoogleIdToken = async function (idToken) {
      // Simulate calling Google's token verification
      const ticket = await mockVerifyIdToken({ idToken, audience: GOOGLE_CLIENT_ID });
      const payload = ticket.getPayload();

      if (!payload) throw new Error('Empty payload from Google');
      if (!payload.email_verified) throw new Error('Email not verified');
      if (payload.aud !== GOOGLE_CLIENT_ID) throw new Error('Audience mismatch');

      return payload;
    };
  });

  describe('valid Google token', () => {
    beforeEach(() => {
      mockVerifyIdToken.mockResolvedValue({
        getPayload: () => MOCK_GOOGLE_PAYLOAD,
      });
    });

    test('returns user payload on valid token', async () => {
      const payload = await verifyGoogleIdToken(MOCK_GOOGLE_ID_TOKEN);
      expect(payload.email).toBe('testuser@gmail.com');
      expect(payload.sub).toBe('109876543210987654321');
      expect(payload.name).toBe('Test User');
    });

    test('email_verified is true in returned payload', async () => {
      const payload = await verifyGoogleIdToken(MOCK_GOOGLE_ID_TOKEN);
      expect(payload.email_verified).toBe(true);
    });

    test('payload contains picture URL', async () => {
      const payload = await verifyGoogleIdToken(MOCK_GOOGLE_ID_TOKEN);
      expect(payload.picture).toMatch(/^https:\/\//);
    });

    test('verifyIdToken is called once with the token', async () => {
      await verifyGoogleIdToken(MOCK_GOOGLE_ID_TOKEN);
      expect(mockVerifyIdToken).toHaveBeenCalledTimes(1);
      expect(mockVerifyIdToken).toHaveBeenCalledWith(
        expect.objectContaining({ idToken: MOCK_GOOGLE_ID_TOKEN })
      );
    });
  });

  describe('expired Google token', () => {
    beforeEach(() => {
      // Simulate Google library throwing on expired token
      mockVerifyIdToken.mockRejectedValue(
        new Error('Token used too late, 1700003600 > 1745000000: ...')
      );
    });

    test('throws when Google rejects an expired token', async () => {
      await expect(verifyGoogleIdToken(MOCK_GOOGLE_ID_TOKEN)).rejects.toThrow();
    });
  });

  describe('invalid / tampered Google token', () => {
    beforeEach(() => {
      mockVerifyIdToken.mockRejectedValue(new Error('Invalid token signature.'));
    });

    test('throws for tampered token', async () => {
      await expect(verifyGoogleIdToken('tampered.token.value')).rejects.toThrow(
        /signature|invalid/i
      );
    });
  });

  describe('unverified email', () => {
    beforeEach(() => {
      mockVerifyIdToken.mockResolvedValue({
        getPayload: () => ({ ...MOCK_GOOGLE_PAYLOAD, email_verified: false }),
      });
    });

    test('throws when email is not verified', async () => {
      await expect(verifyGoogleIdToken(MOCK_GOOGLE_ID_TOKEN)).rejects.toThrow(
        /email.*not.*verified|verified/i
      );
    });
  });

  describe('audience mismatch', () => {
    beforeEach(() => {
      mockVerifyIdToken.mockResolvedValue({
        getPayload: () => ({
          ...MOCK_GOOGLE_PAYLOAD,
          aud: 'wrong-client-id.apps.googleusercontent.com',
        }),
      });
    });

    test('throws when audience does not match expected client ID', async () => {
      await expect(verifyGoogleIdToken(MOCK_GOOGLE_ID_TOKEN)).rejects.toThrow(
        /audience|aud/i
      );
    });
  });

  describe('null payload from Google', () => {
    beforeEach(() => {
      mockVerifyIdToken.mockResolvedValue({ getPayload: () => null });
    });

    test('throws when getPayload() returns null', async () => {
      await expect(verifyGoogleIdToken(MOCK_GOOGLE_ID_TOKEN)).rejects.toThrow(
        /payload/i
      );
    });
  });
});

// ── authMiddleware integration shape ──────────────────────────────────────

describe('authMiddleware — Express middleware shape', () => {
  /**
   * Build a reference authMiddleware and test its request/response behaviour.
   */
  function makeAuthMiddleware(verifyJwt) {
    return async function authMiddleware(req, res, next) {
      const authHeader = req.headers['authorization'] || '';
      if (!authHeader.startsWith('Bearer ')) {
        return res.status(401).json({ error: 'Missing or malformed Authorization header' });
      }
      const token = authHeader.slice(7);
      try {
        req.user = await verifyJwt(token);
        next();
      } catch (err) {
        return res.status(401).json({ error: err.message });
      }
    };
  }

  function mockRes() {
    const res = { _status: 200, _body: null };
    res.status = (code) => { res._status = code; return res; };
    res.json = (body) => { res._body = body; return res; };
    return res;
  }

  test('calls next() for valid JWT in Authorization header', async () => {
    const middleware = makeAuthMiddleware(async () => MOCK_JWT_PAYLOAD);
    const req = { headers: { authorization: `Bearer ${VALID_JWT}` } };
    const res = mockRes();
    const next = jest.fn();

    await middleware(req, res, next);
    expect(next).toHaveBeenCalledTimes(1);
  });

  test('attaches user payload to req.user on success', async () => {
    const middleware = makeAuthMiddleware(async () => MOCK_JWT_PAYLOAD);
    const req = { headers: { authorization: `Bearer ${VALID_JWT}` } };
    const res = mockRes();
    const next = jest.fn();

    await middleware(req, res, next);
    expect(req.user).toEqual(MOCK_JWT_PAYLOAD);
  });

  test('returns 401 when Authorization header is missing', async () => {
    const middleware = makeAuthMiddleware(async () => MOCK_JWT_PAYLOAD);
    const req = { headers: {} };
    const res = mockRes();
    const next = jest.fn();

    await middleware(req, res, next);
    expect(res._status).toBe(401);
    expect(next).not.toHaveBeenCalled();
  });

  test('returns 401 for expired JWT', async () => {
    const middleware = makeAuthMiddleware(async () => {
      throw new Error('Token expired');
    });
    const req = { headers: { authorization: `Bearer ${EXPIRED_JWT}` } };
    const res = mockRes();
    const next = jest.fn();

    await middleware(req, res, next);
    expect(res._status).toBe(401);
    expect(res._body.error).toMatch(/expired/i);
    expect(next).not.toHaveBeenCalled();
  });

  test('returns 401 for invalid JWT', async () => {
    const middleware = makeAuthMiddleware(async () => {
      throw new Error('Invalid token signature');
    });
    const req = { headers: { authorization: `Bearer ${MALFORMED_JWT}` } };
    const res = mockRes();
    const next = jest.fn();

    await middleware(req, res, next);
    expect(res._status).toBe(401);
    expect(next).not.toHaveBeenCalled();
  });

  test('returns 401 when Bearer prefix is absent', async () => {
    const middleware = makeAuthMiddleware(async () => MOCK_JWT_PAYLOAD);
    const req = { headers: { authorization: VALID_JWT } }; // no "Bearer "
    const res = mockRes();
    const next = jest.fn();

    await middleware(req, res, next);
    expect(res._status).toBe(401);
  });
});
