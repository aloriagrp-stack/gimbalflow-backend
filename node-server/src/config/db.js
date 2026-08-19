const mysql = require('mysql2/promise');

// In-Memory Storage Fallback Data (Active if MySQL is unavailable)
const memoryDb = {
  users: [
    {
      id: 'usr-demo-01',
      email: 'director@gimbalflow.ai',
      name: 'Alex Rivera',
      avatar_url: 'https://image.pollinations.ai/prompt/cinematic%20portrait%20of%20a%20woman%20neon%20cyan%20rim%20light%20dark%20studio?width=200&height=200&seed=501&model=flux&nologo=true',
      credits_balance: 2450,
      plan_tier: 'Pro Director'
    }
  ],
  projects: [
    { id: 'proj-1', user_id: 'usr-demo-01', title: 'TOKYO NIGHT 2099', type: 'cinema', scenesCount: 12, itemsCount: 48, updatedAt: '2 hours ago', tag: 'Cinema Film' },
    { id: 'proj-2', user_id: 'usr-demo-01', title: 'CYBERPUNK CHASE SCENE', type: 'video', scenesCount: 4, itemsCount: 16, updatedAt: '1 day ago', tag: '60FPS Video' },
    { id: 'proj-3', user_id: 'usr-demo-01', title: 'DUNE HORIZON KEYFRAMES', type: 'image', scenesCount: 8, itemsCount: 24, updatedAt: '3 days ago', tag: '8K Textures' }
  ],
  assets: [
    { id: 'ast-1', user_id: 'usr-demo-01', name: 'Kira Vance (Protagonist)', type: 'character', tag: 'Soul ID Character', tagClass: 'soul', meta: 'Used in 4 Projects', url: 'https://image.pollinations.ai/prompt/cinematic%20portrait%20of%20a%20woman%20neon%20cyan%20rim%20light%20dark%20studio?width=500&height=500&seed=501&model=flux&nologo=true' },
    { id: 'ast-2', user_id: 'usr-demo-01', name: 'Neo-Tokyo Skydeck 2099', type: 'location', tag: '3D Set', tagClass: 'location', meta: 'Used in 2 Projects', url: 'https://image.pollinations.ai/prompt/cyberpunk%20city%20street%20at%20night%20neon%20signs%20rain%20cinematic?width=500&height=500&seed=502&model=flux&nologo=true' },
    { id: 'ast-3', user_id: 'usr-demo-01', name: 'Blade Runner Cyber Tone', type: 'style', tag: 'Color Style', tagClass: 'style', meta: 'Used in 6 Projects', url: 'https://image.pollinations.ai/prompt/neon%20city%20skyline%20blade%20runner%20fog%20cinematic?width=500&height=500&seed=503&model=flux&nologo=true' }
  ],
  explore: [],
  presets: [
    {
      id: 'pst-1',
      title: 'Cinematic 360° FPV Swoop',
      category: 'Cinematic',
      creator: 'GimbalFlow Official',
      popularity: '12.4k Uses',
      description: 'High-speed FPV drone swoop around character with volumetric lighting.',
      camera: 'FPV Drone Swoop 360°',
      lens: '24mm Wide Anamorphic',
      aspectRatio: '16:9',
      model: 'Seedance v2',
      promptTemplate: '[Subject] walking through [Location], dramatic volumetric rim lighting, 60fps high speed camera trajectory.',
      thumbnail: 'https://image.pollinations.ai/prompt/cyberpunk%20city%20street%20at%20night%20neon%20signs%20rain%20cinematic?width=500&height=500&seed=502&model=flux&nologo=true'
    },
    {
      id: 'pst-2',
      title: 'Soul ID Character Portrait',
      category: 'Character',
      creator: 'GimbalFlow Official',
      popularity: '9.8k Uses',
      description: 'Hyper-detailed 8K portrait render locked to persistent character geometry.',
      camera: 'Portrait 85mm Bokeh',
      lens: '85mm Prime',
      aspectRatio: '1:1',
      model: 'Higgsfield Cinema Pro',
      promptTemplate: 'Studio lighting 8K portrait of @character, shallow depth of field, sharp eyes, cinematic color grading.',
      thumbnail: 'https://image.pollinations.ai/prompt/cinematic%20portrait%20of%20a%20woman%20neon%20cyan%20rim%20light%20dark%20studio?width=500&height=500&seed=501&model=flux&nologo=true'
    },
    {
      id: 'pst-3',
      title: 'High-Speed Action Explosion',
      category: 'Action',
      creator: 'Studio-H FX',
      popularity: '7.1k Uses',
      description: 'Dynamic slow-mo action pass with realistic particle physics and camera shake.',
      camera: 'Dolly Push In',
      lens: '35mm Prime Anamorphic',
      aspectRatio: '16:9',
      model: 'ActionDiff v3',
      promptTemplate: '[Action scene] with heavy explosions in background, camera shake, slow motion retiming 0.2x.',
      thumbnail: 'https://image.pollinations.ai/prompt/milky%20way%20over%20mountain%20peaks%20astrophotography?width=500&height=500&seed=504&model=flux&nologo=true'
    }
  ],
  generations: []
};

let pool = null;
let useMySQL = false;

async function initDb() {
  const host = process.env.MYSQL_HOST || 'localhost';
  const user = process.env.MYSQL_USER || 'root';
  const password = process.env.MYSQL_PASSWORD || '';
  const database = process.env.MYSQL_DATABASE || 'gimbalflow_db';
  const port = process.env.MYSQL_PORT || 3306;

  try {
    pool = mysql.createPool({
      host,
      user,
      password,
      database,
      port,
      waitForConnections: true,
      connectionLimit: 10,
      queueLimit: 0,
      connectTimeout: 2000
    });

    const conn = await pool.getConnection();
    console.log(`[MySQL] Connected successfully to ${database} on ${host}:${port}`);
    conn.release();
    useMySQL = true;
    await ensureUserSchema();
  } catch (err) {
    console.warn(`[MySQL Notice] Could not connect to MySQL server (${err.message}). Using Memory Store fallback for seamless execution.`);
    useMySQL = false;
  }
}

async function ensureUserSchema() {
  if (!useMySQL || !pool) return;
  try {
    const [cols] = await pool.query(
      "SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND COLUMN_NAME = 'username'"
    );
    if (cols.length === 0) {
      await pool.query('ALTER TABLE users ADD COLUMN username VARCHAR(50) NULL, ADD UNIQUE KEY uq_users_username (username)');
      console.log('[MySQL] Added users.username column (unique).');
    }
  } catch (err) {
    console.warn('[MySQL] ensureUserSchema failed:', err.message);
  }
}

function getMemoryDb() {
  return memoryDb;
}

function isMySQLActive() {
  return useMySQL;
}

function getPool() {
  return pool;
}

module.exports = {
  initDb,
  getMemoryDb,
  isMySQLActive,
  getPool
};
