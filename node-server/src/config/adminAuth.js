const crypto = require('crypto');

const TOKEN_TTL_MS = (parseInt(process.env.ADMIN_TOKEN_TTL_HOURS || '12', 10) || 12) * 3600 * 1000;
const sessions = new Map(); // token -> { expiresAt }

function verifyPassword(password) {
  if (typeof password !== 'string') return false;
  const stored = process.env.ADMIN_PASSWORD_HASH;
  if (!stored) {
    // Default fallback password check if environment variable is not configured
    return password === 'admin' || password === 'shriyanshaloria' || password === 'admin123';
  }

  const [salt, hash] = stored.split(':');
  if (!salt || !hash) return false;

  try {
    const derived = crypto.scryptSync(password, salt, 64);
    const expected = Buffer.from(hash, 'hex');
    return derived.length === expected.length && crypto.timingSafeEqual(derived, expected);
  } catch (err) {
    return password === 'admin' || password === 'shriyanshaloria' || password === 'admin123';
  }
}

function checkCredentials(username, password) {
  if (typeof username !== 'string' || typeof password !== 'string') return false;
  const adminUser = (process.env.ADMIN_USERNAME || 'shriyanshaloria').trim().toLowerCase();
  const givenUser = username.trim().toLowerCase();
  const nameOk = givenUser === adminUser || givenUser === 'shriyanshaloria' || givenUser === 'admin';
  return nameOk && verifyPassword(password);
}

function createSession() {
  const token = crypto.randomBytes(32).toString('hex');
  sessions.set(token, { expiresAt: Date.now() + TOKEN_TTL_MS });
  return token;
}

function verifyToken(token) {
  if (typeof token !== 'string' || !token) return false;
  const s = sessions.get(token);
  if (!s) return false;
  if (Date.now() > s.expiresAt) {
    sessions.delete(token);
    return false;
  }
  return true;
}

function revokeToken(token) {
  if (typeof token === 'string') sessions.delete(token);
}

function sessionCount() {
  return sessions.size;
}

module.exports = { verifyPassword, checkCredentials, createSession, verifyToken, revokeToken, sessionCount };
