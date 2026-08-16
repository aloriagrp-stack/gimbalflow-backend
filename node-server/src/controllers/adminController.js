const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { checkCredentials, createSession, verifyToken, revokeToken } = require('../config/adminAuth');

const DATA_DIR = path.join(__dirname, '..', '..', 'data');
const UPLOAD_DIR = path.join(__dirname, '..', '..', 'uploads', 'hero');
const HERO_FILE = path.join(DATA_DIR, 'hero-cards.json');

const DEFAULT_CARDS = [
  { id: 'hero-1', media: 'video', src: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4', poster: 'https://image.pollinations.ai/prompt/cinematic%20portrait%20of%20a%20woman%20neon%20cyan%20rim%20light%20dark%20studio?width=1000&height=562&seed=501&model=flux&nologo=true', title: 'CINEMA STUDIO 4 IS HERE', desc: 'More control. Longer scenes. Sharper quality.', link: '/cinema' },
  { id: 'hero-2', media: 'img', src: 'https://image.pollinations.ai/prompt/silhouette%20person%20neon%20fog%20cinematic%20moody?width=1000&height=562&seed=506&model=flux&nologo=true', title: 'GIMBALFLOW PLUGIN IN CHATGPT', desc: 'All the top models in one place: Seedance 2.5, Seedance 2.0...', link: '/image' },
  { id: 'hero-3', media: 'img', src: 'https://image.pollinations.ai/prompt/neon%20city%20skyline%20blade%20runner%20fog%20cinematic?width=1000&height=562&seed=503&model=flux&nologo=true', title: 'GIMBALFLOW LAYERS', desc: 'Image editor with real-time AI layer decomposition', link: '/image' },
  { id: 'hero-4', media: 'video', src: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyrides.mp4', poster: 'https://image.pollinations.ai/prompt/milky%20way%20over%20mountain%20peaks%20astrophotography?width=1000&height=562&seed=504&model=flux&nologo=true', title: 'SEEDANCE 2.5: CINEMA PASS', desc: 'New episode, 60fps fluid motion model fully integrated', link: '/cinema' },
  { id: 'hero-5', media: 'img', src: 'https://image.pollinations.ai/prompt/cyberpunk%20city%20street%20at%20night%20neon%20signs%20rain%20cinematic?width=1000&height=562&seed=502&model=flux&nologo=true', title: 'THE GIMBALFLOW FILM FESTIVAL', desc: 'Submit your AI short film. Compete for $1M in director grants.', link: null }
];

const DEFAULT_GALLERY = [
  { id: 'gal-1', media: 'video', ratio: 'tall', src: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4', poster: 'https://image.pollinations.ai/prompt/milky%20way%20over%20mountain%20peaks%20astrophotography?width=800&height=1200&seed=504&model=flux&nologo=true' },
  { id: 'gal-2', media: 'img', ratio: 'tall', src: 'https://image.pollinations.ai/prompt/silhouette%20person%20neon%20fog%20cinematic%20moody?width=800&height=1200&seed=506&model=flux&nologo=true' },
  { id: 'gal-3', media: 'img', ratio: 'tall', src: 'https://image.pollinations.ai/prompt/cinematic%20portrait%20of%20a%20woman%20neon%20cyan%20rim%20light%20dark%20studio?width=800&height=1200&seed=501&model=flux&nologo=true' },
  { id: 'gal-4', media: 'video', ratio: 'tall', src: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4', poster: 'https://image.pollinations.ai/prompt/neon%20city%20skyline%20blade%20runner%20fog%20cinematic?width=800&height=1200&seed=503&model=flux&nologo=true' },
  { id: 'gal-5', media: 'img', ratio: 'tall', src: 'https://image.pollinations.ai/prompt/silhouette%20person%20neon%20fog%20cinematic%20moody?width=800&height=1200&seed=506&model=flux&nologo=true' },
  { id: 'gal-6', media: 'img', ratio: 'tall', src: 'https://image.pollinations.ai/prompt/cyberpunk%20city%20street%20at%20night%20neon%20signs%20rain%20cinematic?width=800&height=1200&seed=502&model=flux&nologo=true' },
  { id: 'gal-7', media: 'video', ratio: 'tall', src: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyrides.mp4', poster: 'https://image.pollinations.ai/prompt/milky%20way%20over%20mountain%20peaks%20astrophotography?width=800&height=1200&seed=504&model=flux&nologo=true' },
  { id: 'gal-8', media: 'img', ratio: 'tall', src: 'https://image.pollinations.ai/prompt/neon%20city%20skyline%20blade%20runner%20fog%20cinematic?width=800&height=1200&seed=503&model=flux&nologo=true' },
  { id: 'gal-9', media: 'img', ratio: 'tall', src: 'https://image.pollinations.ai/prompt/abstract%20liquid%20chrome%20waves%20dark%20background?width=800&height=1200&seed=505&model=flux&nologo=true' },
  { id: 'gal-10', media: 'img', ratio: 'tall', src: 'https://image.pollinations.ai/prompt/cinematic%20portrait%20of%20a%20woman%20neon%20cyan%20rim%20light%20dark%20studio?width=800&height=1200&seed=501&model=flux&nologo=true' },
  { id: 'gal-11', media: 'img', ratio: 'square', src: 'https://image.pollinations.ai/prompt/snow%20mountain%20peak%20night%20starry%20sky?width=800&height=800&seed=507&model=flux&nologo=true' }
];

function ensureDirs() {
  fs.mkdirSync(DATA_DIR, { recursive: true });
  fs.mkdirSync(UPLOAD_DIR, { recursive: true });
}

function loadCards() {
  ensureDirs();
  try {
    if (fs.existsSync(HERO_FILE)) {
      const parsed = JSON.parse(fs.readFileSync(HERO_FILE, 'utf8'));
      if (Array.isArray(parsed)) return parsed;
    }
  } catch (err) {
    console.warn('[Admin] Could not read hero-cards.json, using defaults:', err.message);
  }
  return DEFAULT_CARDS;
}

let heroCards = loadCards();

function saveCards() {
  ensureDirs();
  try {
    fs.writeFileSync(HERO_FILE, JSON.stringify(heroCards, null, 2));
  } catch (err) {
    console.error('[Admin] Failed to persist hero cards:', err.message);
  }
}

// ─── Gallery (below hero) ────────────────────────────────────────
const GALLERY_FILE = path.join(DATA_DIR, 'gallery.json');

function loadGallery() {
  ensureDirs();
  try {
    if (fs.existsSync(GALLERY_FILE)) {
      const parsed = JSON.parse(fs.readFileSync(GALLERY_FILE, 'utf8'));
      if (Array.isArray(parsed)) return parsed;
    }
  } catch (err) {
    console.warn('[Admin] Could not read gallery.json, using defaults:', err.message);
  }
  return DEFAULT_GALLERY;
}

let gallery = loadGallery();

function saveGalleryFile() {
  ensureDirs();
  try {
    fs.writeFileSync(GALLERY_FILE, JSON.stringify(gallery, null, 2));
  } catch (err) {
    console.error('[Admin] Failed to persist gallery:', err.message);
  }
}

// ─── Media upload (base64 data URL → file on disk) ───────────────
const EXT_BY_MIME = {
  'image/jpeg': 'jpg',
  'image/png': 'png',
  'image/webp': 'webp',
  'image/gif': 'gif',
  'video/mp4': 'mp4',
  'video/webm': 'webm',
  'video/quicktime': 'mov'
};

function saveMedia(dataUrl) {
  if (typeof dataUrl !== 'string') {
    console.warn('[Admin] saveMedia: no dataUrl provided');
    return null;
  }
  const match = dataUrl.match(/^data:([a-z0-9-]+\/[a-z0-9-]+);base64,(.+)$/i);
  if (!match) {
    console.warn('[Admin] saveMedia: invalid data URL (length=' + dataUrl.length + ', prefix=' + dataUrl.slice(0, 40) + ')');
    return null;
  }
  const mime = match[1].toLowerCase();
  const ext = EXT_BY_MIME[mime];
  if (!ext) {
    console.warn('[Admin] saveMedia: unsupported mime ' + mime);
    return null;
  }

  const buffer = Buffer.from(match[2], 'base64');
  if (buffer.length === 0) {
    console.warn('[Admin] saveMedia: empty buffer');
    return null;
  }
  if (buffer.length > 160 * 1024 * 1024) {
    console.warn('[Admin] saveMedia: file too large ' + buffer.length);
    return null;
  }

  const name = `${Date.now()}-${crypto.randomBytes(6).toString('hex')}.${ext}`;
  try {
    fs.writeFileSync(path.join(UPLOAD_DIR, name), buffer);
  } catch (err) {
    console.error('[Admin] saveMedia: write failed:', err.message);
    return null;
  }
  return `/uploads/hero/${name}`;
}

function deleteMedia(urlPath) {
  if (typeof urlPath !== 'string' || !urlPath.startsWith('/uploads/')) return;
  const abs = path.join(UPLOAD_DIR, path.basename(urlPath));
  try {
    if (fs.existsSync(abs)) fs.unlinkSync(abs);
  } catch (err) {
    console.warn('[Admin] Could not delete media file:', err.message);
  }
}

// ─── Auth handlers ────────────────────────────────────────────────
function login(req, res) {
  const { username, password } = req.body || {};
  if (!process.env.ADMIN_USERNAME || !process.env.ADMIN_PASSWORD_HASH) {
    return res.status(500).json({ error: 'Admin credentials are not configured on the server.' });
  }
  if (!checkCredentials(username, password)) {
    return res.status(401).json({ error: 'Invalid username or password.' });
  }
  const token = createSession();
  res.json({ token, expiresInHours: parseInt(process.env.ADMIN_TOKEN_TTL_HOURS || '12', 10) || 12 });
}

function logout(req, res) {
  const header = req.headers.authorization || '';
  const token = header.startsWith('Bearer ') ? header.slice(7) : '';
  revokeToken(token);
  res.json({ ok: true });
}

function requireAuth(req, res, next) {
  const header = req.headers.authorization || '';
  const token = header.startsWith('Bearer ') ? header.slice(7) : '';
  if (!token || !verifyToken(token)) {
    return res.status(401).json({ error: 'Unauthorized. Valid admin session required.' });
  }
  next();
}

// ─── Hero cards ──────────────────────────────────────────────────
// Public — used by the Explore page to render the hero showcase.
function getHeroCards(req, res) {
  res.json(heroCards);
}

// Public — metadata about the admin module (used by panel overview).
function getAdminInfo(req, res) {
  res.json({ sessions: require('../config/adminAuth').sessionCount(), heroCards: heroCards.length });
}

// Admin — replace the whole hero deck (title/desc/media/src/poster).
// Never fails on media: cards without media inherit the previous version,
// brand-new cards without media are skipped. Saved state is always kept.
function saveHeroCards(req, res) {
  const { cards } = req.body || {};
  if (!Array.isArray(cards)) {
    return res.status(400).json({ error: 'cards must be an array.' });
  }

  const refreshed = [];
  const validLinks = ['/cinema', '/image', '/explore', '/profile'];
  for (const c of cards) {
    const prev = heroCards.find((h) => h.id === c.id) || null;

    const title = typeof c.title === 'string' ? c.title.trim().slice(0, 80) : '';
    const desc = typeof c.desc === 'string' ? c.desc.trim().slice(0, 160) : (prev ? prev.desc : '');
    const media = c.media === 'video' ? 'video' : 'img';
    const link = validLinks.includes(c.link) ? c.link : (prev ? (validLinks.includes(prev.link) ? prev.link : null) : null);

    let src = typeof c.src === 'string' && c.src ? c.src : (prev && prev.src ? prev.src : '');
    let poster = typeof c.poster === 'string' && c.poster ? c.poster : (prev && prev.poster ? prev.poster : '');

    // If a fresh upload was supplied, persist it to disk and remove the old file.
    const newSrc = saveMedia(c.srcData);
    if (newSrc) {
      deleteMedia(src);
      src = newSrc;
    }
    const newPoster = saveMedia(c.posterData);
    if (newPoster) {
      deleteMedia(poster);
      poster = newPoster;
    }

    // Brand-new card without any media → skip it instead of failing the save.
    if (!prev && (!title || !src)) continue;

    refreshed.push({ id: c.id || `hero-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`, media, src: src || '', poster: poster || '', title: title || (prev ? prev.title : ''), desc, link });
  }

  heroCards = refreshed;
  saveCards();
  res.json({ ok: true, cards: heroCards });
}

// Public — gallery grid below the hero section.
function getGallery(req, res) {
  res.json(gallery);
}

// Admin — replace the whole gallery deck.
// Never fails on media: items without media inherit the previous version,
// brand-new items without media are skipped. Saved state is always kept.
function saveGallery(req, res) {
  const { items } = req.body || {};
  if (!Array.isArray(items)) {
    return res.status(400).json({ error: 'items must be an array.' });
  }

  const refreshed = [];
  for (const it of items) {
    const prev = gallery.find((g) => g.id === it.id) || null;
    const media = it.media === 'video' ? 'video' : 'img';
    // Gallery supports 9:16 portrait cards + square accent cards only.
    const ratio = it.ratio === 'square' ? 'square' : 'tall';

    let src = typeof it.src === 'string' && it.src ? it.src : (prev && prev.src ? prev.src : '');
    let poster = typeof it.poster === 'string' && it.poster ? it.poster : (prev && prev.poster ? prev.poster : '');

    const newSrc = saveMedia(it.srcData);
    if (newSrc) {
      deleteMedia(src);
      src = newSrc;
    }
    const newPoster = saveMedia(it.posterData);
    if (newPoster) {
      deleteMedia(poster);
      poster = newPoster;
    }

    // Brand-new item without any media → skip it instead of failing the save.
    if (!prev && !src) continue;

    refreshed.push({ id: it.id || `gal-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`, media, ratio, src: src || '', poster: poster || '' });
  }

  gallery = refreshed;
  saveGalleryFile();
  res.json({ ok: true, items: gallery });
}

module.exports = { login, logout, requireAuth, getHeroCards, saveHeroCards, getGallery, saveGallery, getAdminInfo };