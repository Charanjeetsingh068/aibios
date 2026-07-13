import dotenv from 'dotenv';
import path from 'path';

// Load env variables
dotenv.config(); // Loads .env in current working directory (backend/.env or root .env)

export const config = {
  port: process.env.PORT || process.env.BACKEND_PORT || 8000,
  mongoUri: process.env.MONGODB_URL || 'mongodb://localhost:27017/aibios_nosql',
  redisHost: process.env.REDIS_HOST || 'localhost',
  redisPort: process.env.REDIS_PORT || 6379,
  redisPassword: process.env.REDIS_PASSWORD || '',
  jwtSecret: process.env.SECRET_KEY || 'generate_a_secure_token_secret_for_jwt_2026_enterprise',
  accessTokenExpiry: '15m',
  refreshTokenExpiry: '7d',
  rememberMeTokenExpiry: '30d',
  environment: process.env.ENVIRONMENT || 'development',
  frontendUrl: process.env.FRONTEND_URL || 'http://localhost:3000'
};
