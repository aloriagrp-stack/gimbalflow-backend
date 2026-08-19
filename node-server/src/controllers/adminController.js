const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { checkCredentials, createSession, verifyToken, revokeToken } = require('../config/adminAuth');

const DATA_DIR = path.join(__dirname, '..', '..', 'data');
const UPLOAD_DIR = path.join(__dirname, '..', '..', 'uploads', 'hero');
const HERO_FILE = path.join(DATA_DIR, 'hero-cards.json');

const DEFAULT_CARDS = [];

const DEFAULT_GALLERY = [];

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
  if (typeof dataUrl !== 'string' || !dataUrl) return null;
  
  if (dataUrl.startsWith('/uploads/') || dataUrl.startsWith('http://') || dataUrl.startsWith('https://')) {
    return dataUrl;
  }

  const match = dataUrl.match(/^data:([^;]+);base64,(.+)$/i);
  if (!match) {
    console.warn('[Admin] saveMedia: invalid data URL format');
    return null;
  }

  const rawMime = match[1].toLowerCase().trim().split(';')[0];
  let ext = EXT_BY_MIME[rawMime];
  if (!ext) {
    if (rawMime.startsWith('video/')) ext = 'mp4';
    else if (rawMime.startsWith('image/')) ext = 'jpg';
    else ext = 'bin';
  }

  const buffer = Buffer.from(match[2], 'base64');
  if (buffer.length === 0) {
    console.warn('[Admin] saveMedia: empty buffer');
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