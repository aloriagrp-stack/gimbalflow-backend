const { isMySQLActive, getPool, getMemoryDb } = require('../config/db');
const { requireUser } = require('./authController');

// Mirrors the frontend reserved list — server is the source of truth for live site
const RESERVED_USERNAMES = [
  'admin', 'gimbalflow', 'gimbal', 'director', 'soul', 'soulid', 'support',
  'staff', 'official', 'moderator', 'system', 'guest', 'gimbalflowapp',
  'shriyanshaloria', 'shriyansh', 'loria', 'newuser', 'user', 'profile'
];

function validateName(v) {
  const s = String(v).trim();
  if (s.length < 2 || s.length > 80) return null;
  return s;
}

function validateUsername(v) {
  const u = String(v).trim().toLowerCase();
  if (!/^[a-z0-9_.]{3,20}$/.test(u)) return null;
  return u;
}

async function getUserProfile(req, res) {
  try {
    const user = await requireUser(req);
    if (!user) {
      return res.status(401).json({ error: 'Unauthorized. Sign in first.' });
    }
    return res.json(user);
  } catch (err) {
    console.error('getUserProfile error:', err);
    res.status(500).json({ error: 'Failed to fetch user profile' });
  }
}

// PUT /api/user/profile — signed-in user updates own name/username/avatar
async function updateUserProfile(req, res) {
  try {
    const user = await requireUser(req);
    if (!user) return res.status(401).json({ error: 'Unauthorized. Sign in first.' });

    const { name, username, avatar_url } = req.body || {};
    const updates = {};

    if (name !== undefined) {
      const valid = validateName(name);
      if (!valid) return res.status(400).json({ error: 'Name must be 2-80 characters.' });
      updates.name = valid;
    }

    if (avatar_url !== undefined) {
      const v = String(avatar_url);
      if (v.length > 200000) return res.status(400).json({ error: 'Avatar image is too large.' });
      updates.avatar_url = v;
    }

    if (username !== undefined) {
      const u = validateUsername(username);
      if (!u) {
        return res.status(400).json({ error: 'Username must be 3-20 characters. Letters, numbers, dots and underscores only.' });
      }
      if (RESERVED_USERNAMES.includes(u)) {
        return res.status(400).json({ error: 'This username is reserved.' });
      }
      if (isMySQLActive()) {
        const pool = getPool();
        const [rows] = await pool.query(
          'SELECT id FROM users WHERE username = ? AND id <> ?',
          [u, user.id]
        );
        if (rows.length > 0) return res.status(409).json({ error: 'This username is already taken.' });
      } else {
        const clash = getMemoryDb().users.find((x) => x.username === u && x.id !== user.id);
        if (clash) return res.status(409).json({ error: 'This username is already taken.' });
      }
      updates.username = u;
    }

    if (Object.keys(updates).length === 0) return res.json({ profile: { ...user } });

    if (isMySQLActive()) {
      const pool = getPool();
      const setClause = Object.keys(updates).map((k) => `${k} = ?`).join(', ');
      const values = Object.values(updates);
      await pool.query(`UPDATE users SET ${setClause} WHERE id = ?`, [...values, user.id]);
      const [rows] = await pool.query(
        'SELECT id, email, name, avatar_url, username, credits_balance, plan_tier FROM users WHERE id = ?',
        [user.id]
      );
      if (rows.length > 0) return res.json({ profile: rows[0] });
      return res.json({ profile: { ...user, ...updates } });
    }

    const memoryDb = getMemoryDb();
    const memUser = memoryDb.users.find((u) => u.id === user.id);
    if (!memUser) return res.status(401).json({ error: 'User not found' });
    Object.assign(memUser, updates);
    return res.json({ profile: { ...memUser } });
  } catch (err) {
    console.error('updateUserProfile error:', err);
    res.status(500).json({ error: 'Failed to update profile' });
  }
}

async function deductCredits(req, res) {
  try {
    const user = await requireUser(req);
    if (!user) {
      return res.status(401).json({ error: 'Unauthorized. Sign in first.' });
    }

    const { amount } = req.body;
    const cost = Number(amount) || 20;

    if (isMySQLActive()) {
      const pool = getPool();
      const [rows] = await pool.query('SELECT credits_balance FROM users WHERE id = ?', [user.id]);
      if (rows.length > 0) {
        const current = rows[0].credits_balance;
        if (current < cost) {
          return res.status(400).json({ error: 'Insufficient credits balance' });
        }
        const updated = current - cost;
        await pool.query('UPDATE users SET credits_balance = ? WHERE id = ?', [updated, user.id]);
        return res.json({ credits_balance: updated });
      }
    }

    const memoryDb = getMemoryDb();
    const memUser = memoryDb.users.find((u) => u.id === user.id);
    if (!memUser) {
      return res.status(401).json({ error: 'User not found' });
    }
    if (memUser.credits_balance < cost) {
      return res.status(400).json({ error: 'Insufficient credits balance' });
    }
    memUser.credits_balance -= cost;
    return res.json({ credits_balance: memUser.credits_balance });
  } catch (err) {
    console.error('deductCredits error:', err);
    res.status(500).json({ error: 'Failed to deduct credits' });
  }
}

module.exports = { getUserProfile, updateUserProfile, deductCredits };