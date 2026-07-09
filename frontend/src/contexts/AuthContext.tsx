"use client";

import { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react';
import { getMe, UserResponse } from '../services/authService';
import { getAccessToken, clearTokens } from '../utils/tokenStorage';

interface AuthContextValue {
  user: UserResponse | null;
  permissions: string[];
  isLoading: boolean;
  isAuthenticated: boolean;
  hasPermission: (permission: string) => boolean;
  hasAnyPermission: (permissionsToCheck: string[]) => boolean;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const loadUser = useCallback(async () => {
    if (!getAccessToken()) {
      setUser(null);
      setIsLoading(false);
      return;
    }
    try {
      const me = await getMe();
      setUser(me);
    } catch {
      clearTokens();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  // A super_admin holds "admin:all" server-side and bypasses every PermissionChecker —
  // mirror that here so the sidebar/route guards don't hide modules from super_admin.
  const hasPermission = useCallback(
    (permission: string) => {
      if (!user) return false;
      if (user.role_id === 'super_admin' || user.permissions.includes('admin:all')) return true;
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
