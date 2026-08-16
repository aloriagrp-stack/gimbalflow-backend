const { isMySQLActive, getPool, getMemoryDb } = require('../config/db');
const { getCache, setCache } = require('../config/redis');

async function getAssets(req, res) {
  try {
    const cacheKey = 'gimbalflow:assets:all';
    const cached = await getCache(cacheKey);
    if (cached) return res.json(cached);

    if (isMySQLActive()) {
      const pool = getPool();
      const [rows] = await pool.query('SELECT * FROM assets ORDER BY created_at DESC');
      await setCache(cacheKey, rows, 60);
      return res.json(rows);
    }

    const memoryDb = getMemoryDb();
    await setCache(cacheKey, memoryDb.assets, 60);
    return res.json(memoryDb.assets);
  } catch (err) {
    console.error('getAssets error:', err);
    res.status(500).json({ error: 'Failed to fetch assets' });
  }
}

async function createAsset(req, res) {
  try {
    const { name, type, tag, tagClass, meta, url } = req.body;
    const newAsset = {
      id: `ast-${Date.now()}`,
      user_id: 'usr-demo-01',
      name: name || 'New Asset Reference',
      type: type || 'image',
      tag: tag || 'Custom Reference',
      tagClass: tagClass || 'soul',
      meta: meta || 'Used in 1 Project',
      url: url || 'https://image.pollinations.ai/prompt/cinematic%20portrait%20of%20a%20woman%20neon%20cyan%20rim%20light%20dark%20studio?width=500&height=500&seed=501&model=flux&nologo=true'
    };

    if (isMySQLActive()) {
      const pool = getPool();
      await pool.query(
        'INSERT INTO assets (id, user_id, name, type, tag, tag_class, meta, url) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        [newAsset.id, newAsset.user_id, newAsset.name, newAsset.type, newAsset.tag, newAsset.tagClass, newAsset.meta, newAsset.url]
      );
    } else {
      const memoryDb = getMemoryDb();
      memoryDb.assets.unshift(newAsset);
    }

    await setCache('gimbalflow:assets:all', null, 0);
    res.status(201).json(newAsset);
  } catch (err) {
    console.error('createAsset error:', err);
    res.status(500).json({ error: 'Failed to create asset' });
  }
}

module.exports = { getAssets, createAsset };
