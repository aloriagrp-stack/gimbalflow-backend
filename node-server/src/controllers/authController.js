// Google Sign-In (via Google Identity Services ID token)
// Token verification uses Google's public tokeninfo endpoint — no Firebase
// admin SDK / service account needed. Results are cached per token.
const { isMySQLActive, getPool, getMemoryDb } = require('../config/db');

const tokenCache = new Map(); // idToken -> { email, name, picture, sub, exp }

const NEW_USER_CREDITS = 2000;
const NEW_USER_PLAN = 'Free';

function bearerToken(req) {
  const header = req.headers.authorization || '';
  if (!header.startsWith('Bearer ')) return null;
  const token = header.slice(7).trim();
  return token || null;
}

async function verifyGoogleToken(idToken) {
  if (typeof idToken !== 'string' || idToken.length < 20) return null;

  const cached = tokenCache.get(idToken);
  if (cached && cached.exp * 1000 > Date.now() - 60 * 1000) return cached;

  let payload = null;

  // Primary: Firebase identitytoolkit lookup (canonical for Firebase tokens)
  const apiKey = process.env.FIREBASE_API_KEY;
  if (apiKey) {
    try {
      const ctrl = new AbortController();
      const timer = setTimeout(() => ctrl.abort(), 10000);
      const res = await fetch(
        `https://identitytoolkit.googleapis.com/v1/accounts:lookup?key=${encodeURIComponent(apiKey)}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ idToken }),
          signal: ctrl.signal
        }
      );
      clearTimeout(timer);
      if (res.ok) {
        const data = await res.json();
        const u = data && data.users && data.users[0];
        if (u && u.localId && u.email) {
          const googleInfo = (u.providerUserInfo || []).find((p) => p.providerId === 'google.com');
          payload = {
            sub: String(u.localId).slice(0, 64),
            email: String(u.email).toLowerCase(),
            name: typeof u.displayName === 'string' && u.displayName ? u.displayName.slice(0, 80) : '',
            picture: (googleInfo && googleInfo.photoUrl) || (typeof u.photoUrl === 'string' ? u.photoUrl : ''),
            exp: Number(u.expiresAt || 0) ? Math.floor(Number(u.expiresAt) / 1000) : 0
          };
        }
      }
    } catch (err) {
      console.warn('[Auth] identitytoolkit lookup failed:', err.message);
    }
  }

  // Fallback: Google public tokeninfo endpoint
  if (!payload) {
    try {
      const url = `https://oauth2.googleapis.com/tokeninfo?id_token=${encodeURIComponent(idToken)}`;
      const ctrl = new AbortController();
      const timer = setTimeout(() => ctrl.abort(), 10000);
      const res = await fetch(url, { signal: ctrl.signal });
      clearTimeout(timer);
      if (res.ok) {
        const info = await res.json();
        if (info.sub && info.email && info.email_verified !== 'false' && info.email_verified !== false) {
          payload = {
            sub: String(info.sub).slice(0, 64),
            email: String(info.email).toLowerCase(),
            name: typeof info.name === 'string' ? info.name.slice(0, 80) : '',
            picture: typeof info.picture === 'string' ? info.picture.slice(0, 512) : '',
            exp: Number(info.exp) || 0
          };
        }
      }
    } catch (err) {
      console.warn('[Auth] tokeninfo lookup failed:', err.message);
    }
  }

  if (!payload) {
    console.warn('[Auth] verifyGoogleToken: token could not be verified.');
    return null;
  }

  try { tokenCache.set(idToken, payload); } catch (e) { /* ignore */ }
  if (tokenCache.size > 500) {
    const now = Date.now();
    for (const [k, v] of tokenCache) {
      if (v.exp * 1000 < now) tokenCache.delete(k);
    }
  }
  return payload;
}

function idFromSub(sub) {
  return `usr-${sub}`;
}

function deriveUsername(email) {
  const base = String(email || '').split('@')[0] || '';
  const cleaned = base.toLowerCase().replace(/[^a-z0-9_.]/g, '').slice(0, 20);
  return cleaned || null;
}

async function upsertUser(googleUser) {
  const id = idFromSub(googleUser.sub);
  const username = deriveUsername(googleUser.email);

  if (isMySQLActive()) {
    const pool = getPool();
    try {
      // Google data is used ONLY at creation. Once the user edits their name /
      // avatar / username via the profile API, a later sign-in must NOT
      // overwrite their custom values.
      await pool.query(
        `INSERT INTO users (id, email, name, avatar_url, username, credits_balance, plan_tier)
         VALUES (?, ?, ?, ?, ?, ?, ?)
         ON DUPLICATE KEY UPDATE email = VALUES(email)`,
        [id, googleUser.email, googleUser.name, googleUser.picture || '', username, NEW_USER_CREDITS, NEW_USER_PLAN]
      );
      const [rows] = await pool.query(
        'SELECT id, email, name, avatar_url, username, credits_balance, plan_tier FROM users WHERE id = ?',
        [id]
      );
      if (rows.length > 0) return rows[0];
    } catch (err) {
      console.error('[Auth] MySQL upsert failed, falling back to memory:', err.message);
    }
  }

  // Memory store fallback (kept for the current session only)
  const memoryDb = getMemoryDb();
  let user = memoryDb.users.find((u) => u.id === id || u.email === googleUser.email);
  if (!user) {
    user = {
      id,
      email: googleUser.email,
      name: googleUser.name || 'New User',
      avatar_url: googleUser.picture || '',
      username,
      credits_balance: NEW_USER_CREDITS,
      plan_tier: NEW_USER_PLAN
    };
    memoryDb.users.push(user);
  } else {
    if (user.id !== id) user.id = id;
    if (!user.username) user.username = username;
    if (!user.name) user.name = googleUser.name;
    if (!user.avatar_url && googleUser.picture) user.avatar_url = googleUser.picture;
  }
  return { ...user };
}

async function requireUser(req) {
  const token = bearerToken(req);
  if (!token) return null;
  const googleUser = await verifyGoogleToken(token);
  if (!googleUser) return null;
  return upsertUser(googleUser);
}

// POST /api/auth/verify — frontend sends the Google ID token after sign-in
async function verify(req, res) {
  const { idToken } = req.body || {};
  if (!idToken) return res.status(400).json({ error: 'idToken is required.' });

  const googleUser = await verifyGoogleToken(idToken);
  if (!googleUser) return res.status(401).json({ error: 'Invalid or expired Google token.' });

  const profile = await upsertUser(googleUser);
  res.json({ ok: true, profile });
}

// GET /api/auth/me — validates a persisted token (app boot / refresh)
async function me(req, res) {
  const profile = await requireUser(req);
  if (!profile) return res.status(401).json({ error: 'Unauthorized. Sign in again.' });
  res.json({ profile });
}

module.exports = { verify, me, verifyGoogleToken, requireUser, bearerToken, idFromSub };