const Redis = require('ioredis');

let redisClient = null;
let isRedisConnected = false;
const inMemoryCache = new Map();
const inMemoryQueue = [];

function initRedis() {
  const host = process.env.REDIS_HOST || 'localhost';
  const port = process.env.REDIS_PORT || 6379;

  try {
    redisClient = new Redis({
      host,
      port: Number(port),
      maxRetriesPerRequest: 1,
      connectTimeout: 2000,
      retryStrategy: () => null
    });

    redisClient.on('connect', () => {
      isRedisConnected = true;
      console.log(`[Redis] Connected successfully to ${host}:${port}`);
    });

    redisClient.on('error', (err) => {
      if (isRedisConnected) {
        console.warn('[Redis Notice] Connection lost. Switching to internal cache queue.');
      }
      isRedisConnected = false;
    });
  } catch (err) {
    console.warn(`[Redis Notice] Redis client initialization skipped (${err.message}). Using internal cache queue.`);
    isRedisConnected = false;
  }
}

async function setCache(key, value, ttlSeconds = 300) {
  if (isRedisConnected && redisClient) {
    try {
      await redisClient.set(key, JSON.stringify(value), 'EX', ttlSeconds);
      return;
    } catch (e) {
      // Fallback
    }
  }
  inMemoryCache.set(key, { value, expiresAt: Date.now() + ttlSeconds * 1000 });
}

async function getCache(key) {
  if (isRedisConnected && redisClient) {
    try {
      const data = await redisClient.get(key);
      return data ? JSON.parse(data) : null;
    } catch (e) {
      // Fallback
    }
  }
  const item = inMemoryCache.get(key);
  if (!item) return null;
  if (Date.now() > item.expiresAt) {
    inMemoryCache.delete(key);
    return null;
  }
  return item.value;
}

async function enqueueTask(queueName, taskData) {
  const taskPayload = { id: `task-${Date.now()}`, queueName, taskData, createdAt: new Date() };
  if (isRedisConnected && redisClient) {
    try {
      await redisClient.lpush(queueName, JSON.stringify(taskPayload));
      return taskPayload;
    } catch (e) {
      // Fallback
    }
  }
  inMemoryQueue.push(taskPayload);
  return taskPayload;
}

function getRedisStatus() {
  return {
    connected: isRedisConnected,
    cachedKeys: inMemoryCache.size,
    queuedTasks: inMemoryQueue.length
  };
}

module.exports = {
  initRedis,
  setCache,
  getCache,
  enqueueTask,
  getRedisStatus
};
