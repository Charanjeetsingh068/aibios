"use client";

import { ReactNode, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../contexts/AuthContext';

interface RouteGuardProps {
  children: ReactNode;
  /** Permission required to view this route, e.g. "users:read". Omit to only require login. */
  requiredPermission?: string | string[];
  /** Rendered while the auth check is loading, instead of a redirect flash. */
  fallback?: ReactNode;
}

export function RouteGuard({ children, requiredPermission, fallback = null }: RouteGuardProps) {
  const { isLoading, isAuthenticated, hasPermission, hasAnyPermission } = useAuth();
  const router = useRouter();

  const allowed =
    isAuthenticated &&
    (!requiredPermission ||
      (Array.isArray(requiredPermission) ? hasAnyPermission(requiredPermission) : hasPermission(requiredPermission)));

  useEffect(() => {
    if (isLoading) return;
    if (!isAuthenticated) {
      router.replace('/auth/login');
      return;
    }
    if (!allowed) {
      router.replace('/auth/unauthorized');
    }
  }, [isLoading, isAuthenticated, allowed, router]);

  if (isLoading || !allowed) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}
