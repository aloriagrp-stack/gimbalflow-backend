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

  const base64Idx = dataUrl.indexOf(';base64,');
  if (base64Idx === -1 || !dataUrl.startsWith('data:')) {
    console.warn('[Admin] saveMedia: invalid data URL format');
    return null;
  }

  const header = dataUrl.slice(5, base64Idx);
  const rawMime = header.split(';')[0].toLowerCase().trim();
  const base64Data = dataUrl.slice(base64Idx + 8);

  let ext = EXT_BY_MIME[rawMime];
  if (!ext) {
    if (rawMime.startsWith('video/')) ext = 'mp4';
    else if (rawMime.startsWith('image/')) ext = 'jpg';
    else ext = 'bin';
  }

  const buffer = Buffer.from(base64Data, 'base64');
  if (buffer.length === 0) {
    console.warn('[Admin] saveMedia: empty buffer');
    return null;
  }

  const name = `${Date.now()}-${crypto.randomBytes(6).toString('hex')}.${ext}`;
  try {
    fs.writeFileSync(path.join(UPLOAD_DIR, name), buffer);
    return `/uploads/hero/${name}`;
  } catch (err) {
    console.error('[Admin] saveMedia: write failed:', err.message);
    return null;
  }
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

    const newSrc = saveMedia(c.srcData);
    if (newSrc) {
      deleteMedia(src);
      src = newSrc;
    } else if (!src && typeof c.srcData === 'string' && c.srcData) {
      src = c.srcData;
    }

    const newPoster = saveMedia(c.posterData);
    if (newPoster) {
      deleteMedia(poster);
      poster = newPoster;
    } else if (!poster && typeof c.posterData === 'string' && c.posterData) {
      poster = c.posterData;
    }

    if (!title && !src) continue;

    refreshed.push({
      id: c.id || `hero-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      media,
      src: src || '',
      poster: poster || '',
      title: title || (prev ? prev.title : 'Untitled Card'),
      desc,
      link
    });
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
function saveGallery(req, res) {
  const { items } = req.body || {};
  if (!Array.isArray(items)) {
    return res.status(400).json({ error: 'items must be an array.' });
  }

  const refreshed = [];
  for (const it of items) {
    const prev = gallery.find((g) => g.id === it.id) || null;
    const media = it.media === 'video' ? 'video' : 'img';
    const ratio = it.ratio === 'square' ? 'square' : 'tall';

    let src = typeof it.src === 'string' && it.src ? it.src : (prev && prev.src ? prev.src : '');
    let poster = typeof it.poster === 'string' && it.poster ? it.poster : (prev && prev.poster ? prev.poster : '');

    const newSrc = saveMedia(it.srcData);
    if (newSrc) {
      deleteMedia(src);
      src = newSrc;
    } else if (!src && typeof it.srcData === 'string' && it.srcData) {
      src = it.srcData;
    }

    const newPoster = saveMedia(it.posterData);
    if (newPoster) {
      deleteMedia(poster);
      poster = newPoster;
    } else if (!poster && typeof it.posterData === 'string' && it.posterData) {
      poster = it.posterData;
    }

    if (!src) continue;

    refreshed.push({
      id: it.id || `gal-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      media,
      ratio,
      src: src || '',
      poster: poster || ''
    });
  }

  gallery = refreshed;
  saveGalleryFile();
  res.json({ ok: true, items: gallery });
}

// Admin — direct media file upload endpoint.
function uploadMedia(req, res) {
  const { fileData } = req.body || {};
  if (!fileData) {
    return res.status(400).json({ error: 'fileData is required.' });
  }

  const url = saveMedia(fileData);
  if (!url) {
    return res.status(500).json({ error: 'Failed to save media file on server.' });
  }

  res.json({ ok: true, url });
}

module.exports = { login, logout, requireAuth, getHeroCards, saveHeroCards, getGallery, saveGallery, getAdminInfo, uploadMedia };