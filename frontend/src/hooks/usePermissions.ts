import { useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';

// Определяем разрешения, которые соответствуют ролям
const ROLE_PERMISSIONS: Record<string, string[]> = {
  guest: [],
  user: [
    'files.view_own',
    'files.upload',
    'files.delete_own',
    'censor.use',
    'catalog.view',
    'catalog.manage',
  ],
  admin: [
    'files.view_own',
    'files.view_all',
    'files.upload',
    'files.delete_own',
    'files.delete_all',
    'censor.use',
    'users.view',
    'users.manage',
    'users.delete',
    'catalog.view',
    'catalog.manage',
  ]
};

export const usePermissions = () => {
  const { user } = useAuth();

  const hasRole = useCallback(
    (roleName: string): boolean => {
      if (!user) return false;
      if (user.is_admin) return true;
      return user.roles?.includes(roleName) || false;
    },
    [user]
  );

  const hasPermission = useCallback((permissionName: string): boolean => {
    if (!user) return false;
    if (user.is_admin) return true;

    const userRoles = user.roles || [];
    for (const role of userRoles) {
      const permissions = ROLE_PERMISSIONS[role] || [];
      if (permissions.includes(permissionName)) {
        return true;
      }
    }
    return false;
  }, [user]);

  const hasAnyRole = useCallback(
    (roleNames: string[]): boolean => {
      if (!user) return false;
      if (user.is_admin) return true;
      return roleNames.some((role) => user.roles?.includes(role) || false);
    },
    [user]
  );

  const hasAllRoles = useCallback(
    (roleNames: string[]): boolean => {
      if (!user) return false;
      if (user.is_admin) return true;
      return roleNames.every((role) => user.roles?.includes(role) || false);
    },
    [user]
  );

  return {
    hasRole,
    hasPermission,
    hasAnyRole,
    hasAllRoles,
    isAdmin: user?.is_admin || false,
    userRoles: user?.roles || []
  };
};

