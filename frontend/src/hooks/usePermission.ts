import { useAuth } from '../contexts/AuthContext';

export function usePermission(permission: string | string[]): boolean {
  const { hasPermission, hasAnyPermission } = useAuth();
  if (Array.isArray(permission)) {
    return hasAnyPermission(permission);
  }
  return hasPermission(permission);
}
