import jwt from 'jsonwebtoken';
import { config } from '../config/index.js';
import { redisClient } from '../config/db.js';

/**
 * Generate Access and Refresh JWTs
 */
export function generateTokens(user, roleName, permissions, sessionId, rememberMe = false) {
  const payload = {
    sub: user._id.toString(),
    company_id: user.company_id.toString(),
    role: roleName,
    permissions: permissions,
    sid: sessionId.toString()
  };

  const accessToken = jwt.sign(payload, config.jwtSecret, {
    expiresIn: config.accessTokenExpiry
  });

  const refreshToken = jwt.sign(
    { sub: user._id.toString(), sid: sessionId.toString() },
    config.jwtSecret,
    { expiresIn: rememberMe ? config.rememberMeTokenExpiry : config.refreshTokenExpiry }
  );

  return { accessToken, refreshToken };
}

/**
 * Cache session data in Redis
 */
export async function cacheSession(session, user, roleName, permissions) {
  if (!redisClient || !redisClient.isReady) return;

  const sessionData = JSON.stringify({
    user_id: user._id.toString(),
    company_id: user.company_id.toString(),
    role: roleName,
    permissions: permissions,
    status: user.status
  });

  const ttlSeconds = Math.max(0, Math.floor((new Date(session.expires_at).getTime() - Date.now()) / 1000));
  if (ttlSeconds > 0) {
    await redisClient.set(`session:${session._id.toString()}`, sessionData, {
      EX: ttlSeconds
    });
  }
}

/**
 * Get cached session data from Redis
 */
export async function getCachedSession(sessionId) {
  if (!redisClient || !redisClient.isReady) return null;
  
  const data = await redisClient.get(`session:${sessionId}`);
  return data ? JSON.parse(data) : null;
}

/**
 * Remove session data from Redis
 */
export async function invalidateCachedSession(sessionId) {
  if (!redisClient || !redisClient.isReady) return;
  await redisClient.del(`session:${sessionId}`);
}

/**
 * Verify a JWT token
 */
export function verifyToken(token) {
  try {
    return jwt.verify(token, config.jwtSecret);
  } catch (error) {
    return null;
  }
}
