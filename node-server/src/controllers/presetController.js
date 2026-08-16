const { isMySQLActive, getPool, getMemoryDb } = require('../config/db');
const { getCache, setCache } = require('../config/redis');

async function getPresets(req, res) {
  try {
    const cacheKey = 'gimbalflow:presets:all';
    const cached = await getCache(cacheKey);
    if (cached) return res.json(cached);

    if (isMySQLActive()) {
      const pool = getPool();
      const [rows] = await pool.query('SELECT * FROM presets ORDER BY created_at DESC');
      await setCache(cacheKey, rows, 300);
      return res.json(rows);
    }

    const memoryDb = getMemoryDb();
    await setCache(cacheKey, memoryDb.presets, 300);
    return res.json(memoryDb.presets);
  } catch (err) {
    console.error('getPresets error:', err);
    res.status(500).json({ error: 'Failed to fetch presets' });
  }
}

module.exports = { getPresets };
