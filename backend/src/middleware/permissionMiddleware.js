export function requirePermission(permission) {
  return (req, res, next) => {
    if (!req.user) {
      return res.status(401).json({ detail: 'Authentication required.' });
    }

    // Super Admin or admin:all bypasses permission checker
    if (req.user.role === 'super_admin' || req.user.permissions.includes('admin:all')) {
      return next();
    }

    if (!req.user.permissions.includes(permission)) {
      return res.status(403).json({ detail: `Access denied. Requires '${permission}' permission.` });
    }

    next();
  };
}
