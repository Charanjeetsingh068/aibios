export function restrictTo(...allowedRoles) {
  return (req, res, next) => {
    if (!req.user) {
      return res.status(401).json({ detail: 'Authentication required.' });
    }

    // Super Admin can access everything
    if (req.user.role === 'super_admin') {
      return next();
    }

    if (!allowedRoles.includes(req.user.role)) {
      return res.status(403).json({ detail: 'Access denied. Insufficient role permissions.' });
    }

    next();
  };
}
