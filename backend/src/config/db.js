import { createClient } from 'redis';
import mongoose from 'mongoose';
import { config } from './index.js';

export async function connectMongo() {
  try {
    await mongoose.connect(config.mongoUri);
    console.log('[Database] MongoDB connected successfully.');
  } catch (error) {
    console.error('[Database] MongoDB connection error:', error);
    process.exit(1);
  }
}

// Initialize Redis client
const redisUrl = config.redisPassword 
  ? `redis://:${config.redisPassword}@${config.redisHost}:${config.redisPort}`
  : `redis://${config.redisHost}:${config.redisPort}`;

const redisClient = createClient({ url: redisUrl });

redisClient.on('error', (err) => {
  console.error('[Cache] Redis Client Error:', err.message);
});

redisClient.on('connect', () => {
  console.log('[Cache] Redis connecting...');
});

redisClient.on('ready', () => {
  console.log('[Cache] Redis connected and ready.');
});

export async function connectRedis() {
  try {
    await redisClient.connect();
  } catch (err) {
    console.error('[Cache] Redis connection failed. Redis sessions will fall back to MongoDB:', err.message);
  }
}

export { redisClient };
