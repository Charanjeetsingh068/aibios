import { verifyToken, getCachedSession, cacheSession } from '../utils/tokenUtils.js';
import User from '../models/User.js';
import Session from '../models/Session.js';

export async function authMiddleware(req, res, next) {
  try {
    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({ detail: 'Authentication credentials were not provided.' });
    }

    const token = authHeader.split(' ')[1];
    const decoded = verifyToken(token);
    
    if (!decoded || !decoded.sid) {
      return res.status(401).json({ detail: 'Signature verification failed or token expired.' });
    }

    // 1. Check Redis session cache first
    let sessionData = await getCachedSession(decoded.sid);

    if (!sessionData) {
      // 2. Fallback to MongoDB session lookup
      const session = await Session.findById(decoded.sid);
      if (!session || session.is_revoked || new Date() > session.expires_at) {
        return res.status(401).json({ detail: 'Session is invalid or has expired.' });
      }

      // Populate User and check status
      const user = await User.findById(session.user_id)
        .populate('role_id')
        .populate({ path: 'role_id', populate: { path: 'permissions' } });

      if (!user || user.status !== 'active') {
        return res.status(401).json({ detail: 'User is suspended or deactivated.' });
      }

      const roleName = user.role_id.name;
      const permissions = user.role_id.permissions.map(p => p.name);

      // Re-cache session in Redis
      await cacheSession(session, user, roleName, permissions);

      sessionData = {
        user_id: user._id.toString(),
        company_id: user.company_id.toString(),
        role: roleName,
        permissions: permissions,
        status: user.status
      };
    }

    if (sessionData.status !== 'active') {
      return res.status(401).json({ detail: 'User account is inactive.' });
    }

    // Bind user information to request context
    req.user = {
      id: sessionData.user_id,
      company_id: sessionData.company_id,
      role: sessionData.role,
      permissions: sessionData.permissions
    };
    req.sessionId = decoded.sid;

    next();
  } catch (error) {
    console.error('[Middleware] Authentication error:', error);
    return res.status(500).json({ detail: 'Internal server authentication error.' });
  }
}
