const crypto = require('crypto');

const TOKEN_TTL_MS = (parseInt(process.env.ADMIN_TOKEN_TTL_HOURS || '12', 10) || 12) * 3600 * 1000;
const sessions = new Map(); // token -> { expiresAt }

function verifyPassword(password) {
  const stored = process.env.ADMIN_PASSWORD_HASH;
  const username = process.env.ADMIN_USERNAME;
  if (!stored || !username || typeof password !== 'string') return false;

  const [salt, hash] = stored.split(':');
  if (!salt || !hash) return false;

  const derived = crypto.scryptSync(password, salt, 64);
  const expected = Buffer.from(hash, 'hex');
  return derived.length === expected.length && crypto.timingSafeEqual(derived, expected);
}

function checkCredentials(username, password) {
  if (typeof username !== 'string') return false;
  const expected = Buffer.from(String(process.env.ADMIN_USERNAME || ''), 'utf8');
  const given = Buffer.from(username, 'utf8');
  const nameOk = expected.length === given.length && crypto.timingSafeEqual(expected, given);
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
