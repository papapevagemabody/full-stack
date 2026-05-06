import React, { useState, useEffect } from 'react';
import { usePermissions } from '../hooks/usePermissions';
import { apiService } from '../services/api';
import Seo from '../components/Seo';
import './UserManagement.css';

interface User {
  id: number;
  username: string;
  email?: string;
  is_active: boolean;
  is_admin: boolean;
  roles: string[];
}

interface Role {
  id: number;
  name: string;
  description?: string;
  permissions: string[];
}

const UserManagement: React.FC = () => {
  const { isAdmin } = usePermissions();
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedUser, setSelectedUser] = useState<string | null>(null);
  const [selectedRole, setSelectedRole] = useState<string>('');

  useEffect(() => {
    if (isAdmin) {
      loadData();
    }
  }, [isAdmin]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [usersData, rolesData] = await Promise.all([
        apiService.get('/admin/users'),
        apiService.get('/admin/roles')
      ]);
      setUsers(usersData.users || []);
      setRoles(rolesData.roles || []);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Ошибка при загрузке данных');
      console.error('Error loading data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAssignRole = async (username: string, roleName: string) => {
    try {
      await apiService.post(`/admin/users/${username}/roles/${roleName}`);
      await loadData();
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Ошибка при назначении роли');
      console.error('Error assigning role:', err);
    }
  };

  const handleRemoveRole = async (username: string, roleName: string) => {
    try {
      await apiService.delete(`/admin/users/${username}/roles/${roleName}`);
      await loadData();
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Ошибка при удалении роли');
      console.error('Error removing role:', err);
    }
  };

  if (!isAdmin) {
    return (
      <div className="user-management">
        <div className="access-denied">
          <h2>Доступ запрещен</h2>
          <p>Эта страница доступна только администраторам.</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="user-management">
        <div className="loading">Загрузка...</div>
      </div>
    );
  }

  return (
    <div className="user-management">
      <Seo
        title="Администрирование пользователей"
        description="Назначение ролей и управление учётными записями. Только для администраторов."
        canonicalPath="/admin/users"
        noindex
      />
      <h1>Управление пользователями</h1>
      
      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <div className="users-list">
        <h2>Пользователи</h2>
        <table className="users-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Имя пользователя</th>
              <th>Email</th>
              <th>Роли</th>
              <th>Статус</th>
              <th>Действия</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id}>
                <td>{user.id}</td>
                <td>{user.username}</td>
                <td>{user.email || '-'}</td>
                <td>
                  <div className="roles-list">
                    {user.roles && user.roles.length > 0 ? (
                      user.roles.map((role) => (
                        <span key={role} className="role-badge">
                          {role}
                          <button
                            className="remove-role-btn"
                            onClick={() => handleRemoveRole(user.username, role)}
                            title="Удалить роль"
                          >
                            ×
                          </button>
                        </span>
                      ))
                    ) : (
                      <span className="no-roles">Нет ролей</span>
                    )}
                  </div>
                </td>
                <td>
                  <span className={`status-badge ${user.is_active ? 'active' : 'inactive'}`}>
                    {user.is_active ? 'Активен' : 'Неактивен'}
                  </span>
                  {user.is_admin && <span className="admin-badge">Admin</span>}
                </td>
                <td>
                  <div className="role-assignment">
                    <select
                      value={selectedUser === user.username ? selectedRole : ''}
                      onChange={(e) => {
                        setSelectedUser(user.username);
                        setSelectedRole(e.target.value);
                        if (e.target.value) {
                          handleAssignRole(user.username, e.target.value);
                        }
                      }}
                    >
                      <option value="">Добавить роль...</option>
                      {roles
                        .filter(role => !user.roles?.includes(role.name))
                        .map((role) => (
                          <option key={role.id} value={role.name}>
                            {role.name}
                          </option>
                        ))}
                    </select>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="roles-info">
        <h2>Доступные роли</h2>
        <div className="roles-grid">
          {roles.map((role) => (
            <div key={role.id} className="role-card">
              <h3>{role.name}</h3>
              <p>{role.description || 'Нет описания'}</p>
              <div className="permissions-list">
                <strong>Разрешения:</strong>
                <ul>
                  {role.permissions && role.permissions.length > 0 ? (
                    role.permissions.map((perm, idx) => (
                      <li key={idx}>{perm}</li>
                    ))
                  ) : (
                    <li>Нет разрешений</li>
                  )}
                </ul>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default UserManagement;

