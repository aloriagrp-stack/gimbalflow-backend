const express = require('express');
const router = express.Router();

const { getProjects, createProject } = require('../controllers/projectController');
const { getAssets, createAsset } = require('../controllers/assetController');
const { getPresets } = require('../controllers/presetController');
const { getExploreItems } = require('../controllers/exploreController');
const { getUserProfile, updateUserProfile, deductCredits } = require('../controllers/userController');
const { verify: verifyAuth, me: authMe } = require('../controllers/authController');
const { enhancePrompt, createGenerationJob } = require('../controllers/generationController');
const { login, logout, requireAuth, getHeroCards, saveHeroCards, getGallery, saveGallery, getAdminInfo, uploadMedia } = require('../controllers/adminController');
const { getRedisStatus } = require('../config/redis');
const { isMySQLActive } = require('../config/db');

// System Health & Redis / MySQL status
router.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    gateway: 'GimbalFlow Express API Gateway',
    mysql: isMySQLActive() ? 'connected' : 'memory_fallback',
    redis: getRedisStatus(),
    timestamp: new Date()
  });
});

// User & Credits (Google Sign-In tokens guard these)
router.get('/user/profile', getUserProfile);
router.put('/user/profile', updateUserProfile);
router.post('/user/deduct-credits', deductCredits);

// Google Sign-In session endpoints
router.post('/auth/verify', verifyAuth);
router.get('/auth/me', authMe);

// Projects
router.get('/projects', getProjects);
router.post('/projects', createProject);

// Assets
router.get('/assets', getAssets);
router.post('/assets', createAsset);

// Presets & Explore Feed
router.get('/presets', getPresets);
router.get('/explore', getExploreItems);

// Generation Jobs & Python ML Service Proxy
router.post('/generate/enhance-prompt', enhancePrompt);
router.post('/generate/job', createGenerationJob);

// Hero Section (public — used by the Explore page)
router.get('/hero', getHeroCards);

// Gallery grid (public — used below the hero section)
router.get('/gallery', getGallery);

// Admin (password protected — credentials live only on the server)
router.post('/admin/login', login);
router.post('/admin/logout', logout);
router.get('/admin/info', requireAuth, getAdminInfo);
router.post('/admin/hero', requireAuth, saveHeroCards);
router.post('/admin/gallery', requireAuth, saveGallery);
router.post('/admin/upload', requireAuth, uploadMedia);

module.exports = router;
