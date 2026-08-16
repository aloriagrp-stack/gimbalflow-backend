const { isMySQLActive, getPool, getMemoryDb } = require('../config/db');
const { getCache, setCache } = require('../config/redis');

async function getProjects(req, res) {
  try {
    const cacheKey = 'gimbalflow:projects:all';
    const cached = await getCache(cacheKey);
    if (cached) return res.json(cached);

    if (isMySQLActive()) {
      const pool = getPool();
      const [rows] = await pool.query('SELECT * FROM projects ORDER BY created_at DESC');
      await setCache(cacheKey, rows, 60);
      return res.json(rows);
    }

    const memoryDb = getMemoryDb();
    await setCache(cacheKey, memoryDb.projects, 60);
    return res.json(memoryDb.projects);
  } catch (err) {
    console.error('getProjects error:', err);
    res.status(500).json({ error: 'Failed to fetch projects' });
  }
}

async function createProject(req, res) {
  try {
    const { title, type, scenesCount, itemsCount, tag } = req.body;
    const newProj = {
      id: `proj-${Date.now()}`,
      user_id: 'usr-demo-01',
      title: title || 'Untitled Project',
      type: type || 'video',
      scenesCount: scenesCount || 1,
      itemsCount: itemsCount || 1,
      tag: tag || (type === 'image' ? '8K Textures' : '60FPS Video'),
      updatedAt: 'Just now'
    };

    if (isMySQLActive()) {
      const pool = getPool();
      await pool.query(
        'INSERT INTO projects (id, user_id, title, type, scenes_count, items_count, tag) VALUES (?, ?, ?, ?, ?, ?, ?)',
        [newProj.id, newProj.user_id, newProj.title, newProj.type, newProj.scenesCount, newProj.itemsCount, newProj.tag]
      );
    } else {
      const memoryDb = getMemoryDb();
      memoryDb.projects.unshift(newProj);
    }

    // Invalidate cache
    await setCache('gimbalflow:projects:all', null, 0);
    res.status(201).json(newProj);
  } catch (err) {
    console.error('createProject error:', err);
    res.status(500).json({ error: 'Failed to create project' });
  }
}

module.exports = { getProjects, createProject };
