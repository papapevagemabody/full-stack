import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import RoleProtectedRoute from '../RoleProtectedRoute';
import { useAuth } from '../../../contexts/AuthContext';

jest.mock('../../../contexts/AuthContext', () => ({
  useAuth: jest.fn(),
}));

const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;

describe('RoleProtectedRoute (лаб. №5)', () => {
  beforeEach(() => {
    mockUseAuth.mockReset();
  });

  it('редирект на /login если нет пользователя', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isLoading: false,
    } as any);

    render(
      <MemoryRouter initialEntries={['/secret']}>
        <Routes>
          <Route
            path="/secret"
            element={
              <RoleProtectedRoute>
                <div>Секрет</div>
              </RoleProtectedRoute>
            }
          />
          <Route path="/login" element={<div>Страница входа</div>} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText('Страница входа')).toBeInTheDocument();
  });

  it('показывает детей при загрузке ролей (админ)', () => {
    mockUseAuth.mockReturnValue({
      user: { username: 'a', roles: ['user'], is_admin: true },
      isLoading: false,
    } as any);

    render(
      <MemoryRouter>
        <RoleProtectedRoute requiredRoles={['admin']}>
          <span>Админ-контент</span>
        </RoleProtectedRoute>
      </MemoryRouter>
    );

    expect(screen.getByText('Админ-контент')).toBeInTheDocument();
  });
});
