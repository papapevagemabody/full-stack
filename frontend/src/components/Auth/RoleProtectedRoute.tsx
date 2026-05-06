import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

interface RoleProtectedRouteProps {
  children: React.ReactNode;
  requiredRoles?: string[];
  requireAll?: boolean; // Если true, требуются все роли, если false - хотя бы одна
}

const RoleProtectedRoute: React.FC<RoleProtectedRouteProps> = ({ 
  children, 
  requiredRoles = [],
  requireAll = false 
}) => {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Проверка авторизации...</p>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // Если роли не указаны, проверяем только авторизацию
  if (requiredRoles.length === 0) {
    return <>{children}</>;
  }

  // Проверяем роли пользователя
  const userRoles = user.roles || [];
  const isAdmin = user.is_admin || false;
  
  // Администратор имеет доступ ко всему
  if (isAdmin) {
    return <>{children}</>;
  }

  // Проверяем наличие требуемых ролей
  let hasAccess = false;
  if (requireAll) {
    // Требуются все роли
    hasAccess = requiredRoles.every(role => userRoles.includes(role));
  } else {
    // Требуется хотя бы одна роль
    hasAccess = requiredRoles.some(role => userRoles.includes(role));
  }

  if (!hasAccess) {
    return (
      <div className="access-denied">
        <h2>Доступ запрещен</h2>
        <p>У вас нет необходимых прав для доступа к этой странице.</p>
        <p>Требуемые роли: {requiredRoles.join(', ')}</p>
        <p>Ваши роли: {userRoles.length > 0 ? userRoles.join(', ') : 'нет ролей'}</p>
        <Navigate to="/" replace />
      </div>
    );
  }

  return <>{children}</>;
};

export default RoleProtectedRoute;

