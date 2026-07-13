"use client";

import { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react';
import { getMe, logout as apiLogout } from '../services/authService';
import { getAccessToken, clearTokens } from '../utils/tokenStorage';

export interface WorkspaceResponse {
  id: string;
  name: string;
  slug: string;
}

export interface UserResponse {
  id: string;
  organization_id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  status: string;
  role_id: string;
  timezone: string;
  language: string;
  created_at: string;
  updated_at: string;
  last_login?: string;
  permissions: string[];
  workspaces: WorkspaceResponse[];
}

interface AuthContextValue {
  user: UserResponse | null;
  permissions: string[];
  isLoading: boolean;
  isAuthenticated: boolean;
  hasPermission: (permission: string) => boolean;
  hasAnyPermission: (permissionsToCheck: string[]) => boolean;
  refreshUser: () => Promise<void>;
  workspaces: WorkspaceResponse[];
  currentWorkspace: WorkspaceResponse | null;
  switchWorkspace: (workspaceId: string) => void;
  logoutUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [workspaces, setWorkspaces] = useState<WorkspaceResponse[]>([]);
  const [currentWorkspace, setCurrentWorkspace] = useState<WorkspaceResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const loadUser = useCallback(async () => {
    if (!getAccessToken()) {
      setUser(null);
      setWorkspaces([]);
      setCurrentWorkspace(null);
      setIsLoading(false);
      return;
    }
    try {
      const me = await getMe() as any;
      setUser(me);
      
      const userWorkspaces = me.workspaces || [];
      setWorkspaces(userWorkspaces);

      // Determine active workspace
      const savedWorkspaceId = localStorage.getItem('aibos_current_workspace_id');
      const activeWS = userWorkspaces.find((w: any) => w.id === savedWorkspaceId) || userWorkspaces[0] || null;
      
      if (activeWS) {
        localStorage.setItem('aibos_current_workspace_id', activeWS.id);
        setCurrentWorkspace(activeWS);
      } else {
        setCurrentWorkspace(null);
      }
    } catch (err) {
      console.error('Failed to load user profile:', err);
      clearTokens();
      localStorage.removeItem('aibos_current_workspace_id');
      setUser(null);
      setWorkspaces([]);
      setCurrentWorkspace(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  const switchWorkspace = useCallback((workspaceId: string) => {
    const ws = workspaces.find(w => w.id === workspaceId);
    if (ws) {
      localStorage.setItem('aibos_current_workspace_id', ws.id);
      setCurrentWorkspace(ws);
      // Reload page to re-fetch workspace specific data
      window.location.reload();
    }
  }, [workspaces]);

  const logoutUser = useCallback(async () => {
    setIsLoading(true);
    try {
      await apiLogout();
    } catch (err) {
      console.error('Logout error ignored:', err);
    } finally {
      clearTokens();
      localStorage.removeItem('aibos_current_workspace_id');
      setUser(null);
      setWorkspaces([]);
      setCurrentWorkspace(null);
      setIsLoading(false);
      window.location.href = '/auth/login';
    }
  }, []);

  const hasPermission = useCallback(
    (permission: string) => {
      if (!user) return false;
      // Super Admin holds global access bypass
      if (user.role_id === 'super_admin' || user.permissions.includes('admin:all') || user.permissions.includes('admin.all')) {
        return true;
      }
      return user.permissions.includes(permission);
    },
    [user]
  );

  const hasAnyPermission = useCallback(
    (permissionsToCheck: string[]) => permissionsToCheck.some(hasPermission),
    [hasPermission]
  );

  return (
    <AuthContext.Provider
      value={{
        user,
        permissions: user?.permissions ?? [],
        isLoading,
        isAuthenticated: !!user,
        hasPermission,
        hasAnyPermission,
        refreshUser: loadUser,
        workspaces,
        currentWorkspace,
        switchWorkspace,
        logoutUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
}
