"use client";

import { ReactNode } from 'react';
import { useAuth } from '../contexts/AuthContext';

interface RequirePermissionProps {
  children: ReactNode;
  permission: string | string[];
}

export function RequirePermission({ children, permission }: RequirePermissionProps) {
  const { hasPermission, hasAnyPermission, isAuthenticated } = useAuth();

  if (!isAuthenticated) return null;

  const allowed = Array.isArray(permission) ? hasAnyPermission(permission) : hasPermission(permission);

  if (!allowed) {
    return null;
  }

  return <>{children}</>;
}
