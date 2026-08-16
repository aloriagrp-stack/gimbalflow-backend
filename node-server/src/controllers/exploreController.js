const { isMySQLActive, getPool, getMemoryDb } = require('../config/db');
const { getCache, setCache } = require('../config/redis');

async function getExploreItems(req, res) {
  try {
    const cacheKey = 'gimbalflow:explore:all';
    const cached = await getCache(cacheKey);
    if (cached) return res.json(cached);

    if (isMySQLActive()) {
      const pool = getPool();
      const [rows] = await pool.query('SELECT * FROM explore_items ORDER BY likes DESC');
      await setCache(cacheKey, rows, 120);
      return res.json(rows);
    }

    const memoryDb = getMemoryDb();
    await setCache(cacheKey, memoryDb.explore, 120);
    return res.json(memoryDb.explore);
  } catch (err) {
    console.error('getExploreItems error:', err);
    res.status(500).json({ error: 'Failed to fetch explore feed' });
  }
}

module.exports = { getExploreItems };
