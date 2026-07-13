import Workspace from '../models/Workspace.js';
import User from '../models/User.js';

export async function workspaceMiddleware(req, res, next) {
  try {
    const workspaceId = req.headers['x-workspace-id'];

    if (!workspaceId) {
      // If no workspace ID is provided, continue (some global endpoints don't need it)
      return next();
    }

    // Verify workspace exists
    const workspace = await Workspace.findById(workspaceId);
    if (!workspace || workspace.status !== 'active') {
      return res.status(404).json({ detail: 'Workspace not found or is inactive.' });
    }

    // Super Admin bypasses company and user-assigned checks
    if (req.user.role === 'super_admin') {
      req.workspaceId = workspaceId;
      return next();
    }

    // Verify workspace belongs to user's company
    if (workspace.company_id.toString() !== req.user.company_id) {
      return res.status(403).json({ detail: 'Forbidden. Workspace does not belong to your company.' });
    }

    // Verify user is assigned to this workspace
    const user = await User.findById(req.user.id);
    if (!user || !user.workspaces.includes(workspaceId)) {
      return res.status(403).json({ detail: 'Forbidden. You are not assigned to this workspace.' });
    }

    req.workspaceId = workspaceId;
    next();
  } catch (error) {
    console.error('[Middleware] Workspace isolation error:', error);
    return res.status(500).json({ detail: 'Internal workspace verification error.' });
  }
}
