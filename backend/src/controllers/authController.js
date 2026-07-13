import crypto from 'crypto';
import User from '../models/User.js';
import Company from '../models/Company.js';
import Workspace from '../models/Workspace.js';
import Role from '../models/Role.js';
import Permission from '../models/Permission.js';
import Session from '../models/Session.js';
import ActivityLog from '../models/ActivityLog.js';
import { generateTokens, cacheSession, invalidateCachedSession, verifyToken } from '../utils/tokenUtils.js';

export async function login(req, res) {
  try {
    const { email, password, remember_me } = req.body;
    if (!email || !password) {
      return res.status(400).json({ detail: 'Email and password are required.' });
    }

    const user = await User.findOne({ email: email.toLowerCase() })
      .populate('role_id')
      .populate({ path: 'role_id', populate: { path: 'permissions' } });

    if (!user || !(await user.comparePassword(password))) {
      return res.status(401).json({ detail: 'Authentication failed. Please verify credentials.' });
    }

    if (user.status !== 'active') {
      return res.status(403).json({ detail: 'Your user account is inactive or suspended.' });
    }

    // Verify company is active
    const company = await Company.findById(user.company_id);
    if (!company || company.status !== 'active') {
      return res.status(403).json({ detail: 'Company tenant is inactive.' });
    }

    // Determine session duration based on remember_me
    const sessionDurationDays = remember_me ? 30 : 1;
    const expiresAt = new Date();
    expiresAt.setDate(expiresAt.getDate() + sessionDurationDays);

    // Create session in MongoDB
    const session = await Session.create({
      user_id: user._id,
      company_id: user.company_id,
      refresh_token: 'temp_token_to_be_replaced',
      device_info: req.headers['user-agent'] || 'Unknown',
      ip_address: req.ip || '0.0.0.0',
      expires_at: expiresAt
    });

    const roleName = user.role_id.name;
    const permissions = user.role_id.permissions.map(p => p.name);

    // Generate real JWT tokens
    const { accessToken, refreshToken } = generateTokens(user, roleName, permissions, session._id, remember_me);

    // Update session with correct refresh token
    session.refresh_token = refreshToken;
    await session.save();

    // Cache session in Redis
    await cacheSession(session, user, roleName, permissions);

    // Log Activity
    await ActivityLog.create({
      user_id: user._id,
      company_id: user.company_id,
      action: 'LOGIN',
      description: `User successfully logged in. Remember Me: ${!!remember_me}`,
      ip_address: req.ip,
      device_info: req.headers['user-agent']
    });

    return res.status(200).json({
      access_token: accessToken,
      refresh_token: refreshToken,
      token_type: 'Bearer',
      user_id: user._id.toString(),
      organization_id: user.company_id.toString(),
      role: roleName
    });
  } catch (error) {
    console.error('[AuthController] Login Error:', error);
    return res.status(500).json({ detail: 'Internal server error during login.' });
  }
}

export async function logout(req, res) {
  try {
    if (!req.sessionId) {
      return res.status(400).json({ detail: 'No active session detected.' });
    }

    // Invalidate session in MongoDB
    await Session.findByIdAndUpdate(req.sessionId, { is_revoked: true });

    // Invalidate session in Redis
    await invalidateCachedSession(req.sessionId);

    // Log Activity
    await ActivityLog.create({
      user_id: req.user.id,
      company_id: req.user.company_id,
      action: 'LOGOUT',
      description: 'User successfully logged out.',
      ip_address: req.ip,
      device_info: req.headers['user-agent']
    });

    return res.status(200).json({ message: 'Logout successful.' });
  } catch (error) {
    console.error('[AuthController] Logout Error:', error);
    return res.status(500).json({ detail: 'Internal server error during logout.' });
  }
}

export async function refresh(req, res) {
  try {
    const { refresh_token } = req.body;
    if (!refresh_token) {
      return res.status(400).json({ detail: 'Refresh token is required.' });
    }

    const decoded = verifyToken(refresh_token);
    if (!decoded || !decoded.sid) {
      return res.status(401).json({ detail: 'Invalid or expired refresh token.' });
    }

    const session = await Session.findById(decoded.sid);
    if (!session || session.is_revoked || new Date() > session.expires_at) {
      return res.status(401).json({ detail: 'Session is inactive or has expired.' });
    }

    // Replay Attack Detection: if token is rotated but doesn't match the current session's refresh token
    if (session.refresh_token !== refresh_token) {
      session.is_revoked = true;
      await session.save();
      await invalidateCachedSession(session._id.toString());

      await ActivityLog.create({
        user_id: session.user_id,
        company_id: session.company_id,
        action: 'SECURITY_ALERT',
        description: 'Potential refresh token reuse attack detected! Revoking all sessions.',
        ip_address: req.ip,
        device_info: req.headers['user-agent']
      });

      return res.status(401).json({ detail: 'Token reuse detected. Session terminated.' });
    }

    const user = await User.findById(session.user_id)
      .populate('role_id')
      .populate({ path: 'role_id', populate: { path: 'permissions' } });

    if (!user || user.status !== 'active') {
      return res.status(401).json({ detail: 'User is suspended or deactivated.' });
    }

    const roleName = user.role_id.name;
    const permissions = user.role_id.permissions.map(p => p.name);

    // Rotate tokens
    const { accessToken, refreshToken: newRefreshToken } = generateTokens(
      user,
      roleName,
      permissions,
      session._id,
      session.expires_at.getTime() - Date.now() > 24 * 60 * 60 * 1000 // If remaining time > 1 day, assume remember me
    );

    // Update session refresh token
    session.refresh_token = newRefreshToken;
    await session.save();

    // Cache in Redis
    await cacheSession(session, user, roleName, permissions);

    return res.status(200).json({
      access_token: accessToken,
      refresh_token: newRefreshToken,
      token_type: 'Bearer',
      user_id: user._id.toString(),
      organization_id: user.company_id.toString(),
      role: roleName
    });
  } catch (error) {
    console.error('[AuthController] Refresh Token Error:', error);
    return res.status(500).json({ detail: 'Internal server error during token refresh.' });
  }
}

export async function getMe(req, res) {
  try {
    const user = await User.findById(req.user.id)
      .populate('role_id')
      .populate({ path: 'role_id', populate: { path: 'permissions' } })
      .populate('workspaces');

    if (!user) {
      return res.status(404).json({ detail: 'User profile not found.' });
    }

    // Map company_id to organization_id and role_id to role name for frontend compatibility
    return res.status(200).json({
      id: user._id.toString(),
      organization_id: user.company_id.toString(),
      first_name: user.first_name,
      last_name: user.last_name,
      email: user.email,
      status: user.status,
      role_id: user.role_id.name,
      timezone: user.timezone,
      language: user.language,
      permissions: user.role_id.permissions.map(p => p.name),
      workspaces: user.workspaces.map(w => ({
        id: w._id.toString(),
        name: w.name,
        slug: w.slug
      })),
      created_at: user.created_at,
      updated_at: user.updated_at
    });
  } catch (error) {
    console.error('[AuthController] getMe Error:', error);
    return res.status(500).json({ detail: 'Internal server error fetching user profile.' });
  }
}

export async function getPermissions(req, res) {
  try {
    const permissions = await Permission.find();
    return res.status(200).json(permissions);
  } catch (error) {
    console.error('[AuthController] getPermissions Error:', error);
    return res.status(500).json({ detail: 'Internal server error listing permissions.' });
  }
}

export async function forgotPassword(req, res) {
  try {
    const { email } = req.body;
    if (!email) {
      return res.status(400).json({ detail: 'Email address is required.' });
    }

    const user = await User.findOne({ email: email.toLowerCase() });
    if (!user) {
      // Return 200 for security, avoid email enumeration
      return res.status(200).json({ message: 'If the email exists, a reset link will be provided.' });
    }

    const resetToken = crypto.randomBytes(32).toString('hex');
    user.password_reset_token = resetToken;
    user.password_reset_expires = Date.now() + 3600000; // 1 hour expiry
    await user.save();

    return res.status(200).json({
      message: 'Password reset link has been successfully prepared.',
      token_dev_only: resetToken // Return token for dev console usage as expected by UI
    });
  } catch (error) {
    console.error('[AuthController] Forgot Password Error:', error);
    return res.status(500).json({ detail: 'Internal server error triggering recovery link.' });
  }
}

export async function resetPassword(req, res) {
  try {
    const { token, new_password } = req.body;
    if (!token || !new_password) {
      return res.status(400).json({ detail: 'Token and new password are required.' });
    }

    if (new_password.length < 8) {
      return res.status(400).json({ detail: 'Password must be at least 8 characters long.' });
    }

    const user = await User.findOne({
      password_reset_token: token,
      password_reset_expires: { $gt: Date.now() }
    });

    if (!user) {
      return res.status(400).json({ detail: 'Reset token is invalid or has expired.' });
    }

    // Set new password (the model's pre-save hook will hash it)
    user.password = new_password;
    user.password_reset_token = undefined;
    user.password_reset_expires = undefined;
    await user.save();

    // Revoke all existing sessions for this user for security
    await Session.updateMany({ user_id: user._id }, { is_revoked: true });

    return res.status(200).json({ message: 'Password has been successfully updated.' });
  } catch (error) {
    console.error('[AuthController] Reset Password Error:', error);
    return res.status(500).json({ detail: 'Internal server error during password reset.' });
  }
}
