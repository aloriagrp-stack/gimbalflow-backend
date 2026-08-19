const express = require('express');
const cors = require('cors');
const path = require('path');

// Preserve cPanel Phusion Passenger socket PORT before dotenv
const PASSENGER_PORT = process.env.PORT;

require('dotenv').config({ path: path.join(__dirname, '..', '.env') });

const PORT = PASSENGER_PORT || process.env.PORT || 5000;

const { initDb } = require('./config/db');
const { initRedis } = require('./config/redis');
const apiRoutes = require('./routes/apiRoutes');

const app = express();

// Middleware
app.use(cors({ origin: '*' }));
app.use(express.json({ limit: '200mb' }));
app.use(express.urlencoded({ extended: true, limit: '200mb' }));

// Uploaded media (hero section videos / photos)
app.use('/uploads', express.static(path.join(__dirname, '..', 'uploads')));

// Register API Routes
app.use('/api', apiRoutes);

// Root Status
app.get('/', (req, res) => {
  res.json({
    name: 'GimbalFlow Backend API Gateway',
    status: 'online',
    version: '1.0.0',
    documentation: '/api/health'
  });
});

// Start listening immediately for cPanel Phusion Passenger
const server = app.listen(PORT, () => {
  console.log(`===================================================`);
  console.log(`🚀 GimbalFlow API Gateway running on ${PORT}`);
  console.log(`===================================================`);
  initDb().catch((err) => console.warn('[Db] Init warning:', err.message));
  initRedis();
});

server.on('error', (err) => {
  if (err.code === 'EADDRINUSE') {
    console.error(`❌ Port ${PORT} is already in use.`);
  }
});

module.exports = app;
