const express = require('express');
const cors = require('cors');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '..', '.env') });

const { initDb } = require('./config/db');
const { initRedis } = require('./config/redis');
const apiRoutes = require('./routes/apiRoutes');

const app = express();
const PORT = process.env.PORT || 5000;

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
    version: '1.0.0',
    documentation: '/api/health'
  });
});

async function startServer() {
  await initDb();
  initRedis();

  const server = app.listen(PORT, () => {
    console.log(`===================================================`);
    console.log(`🚀 GimbalFlow API Gateway running on http://localhost:${PORT}`);
    console.log(`📡 Endpoints available at http://localhost:${PORT}/api/health`);
    console.log(`===================================================`);
  });
  server.on('error', (err) => {
    if (err.code === 'EADDRINUSE') {
      console.error(`❌ Port ${PORT} is already in use.`);
      console.error(`   An older GimbalFlow server instance is probably still running.`);
      console.error(`   Close it (Ctrl+C / kill the node process) and start this one,`);
      console.error(`   otherwise the app will keep using the OLD code.`);
      process.exit(1);
    }
    throw err;
  });
}

startServer();
