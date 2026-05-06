// services/authService.ts
import { User, AuthResponse } from '../types/auth';
import { getRefreshTokenCookie } from '../utils/authCookies';
import { getApiBase } from '../config/apiBase';

const API_BASE = getApiBase();

export const authService = {
  async login(username: string, password: string): Promise<AuthResponse> {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    console.log(`🔐 Attempting login for: ${username}`);
    console.log(`🌐 API Base URL: ${API_BASE || '(origin + proxy)'}`);

    try {
      const response = await fetch(`${API_BASE}/token`, {
        method: 'POST',
        body: formData,
        // Не устанавливаем Content-Type - браузер установит автоматически с boundary для FormData
      });

      if (!response.ok) {
        let errorData;
        try {
          errorData = await response.json();
        } catch {
          errorData = { 
            detail: `HTTP ${response.status}: ${response.statusText}` 
          };
        }
        console.error('❌ Login failed:', errorData);
        throw new Error(errorData.detail || `Login failed: ${response.statusText}`);
      }

      const authData: AuthResponse = await response.json();
      if (!authData.refresh_token) {
        console.warn('⚠️ Backend did not return refresh_token');
      }
      console.log('✅ Login successful, tokens received');
      return authData;
    } catch (error: any) {
      // Обработка сетевых ошибок
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        console.error('❌ Network error:', error);
        throw new Error(
          'Не удалось подключиться к API. Запустите uvicorn (порт как в proxy package.json, обычно 8001) или задайте REACT_APP_API_URL.'
        );
      }
      throw error;
    }
  },

  async register(data: { username: string; email?: string; password: string }): Promise<User> {
    console.log(`📝 Starting registration for: ${data.username}`);
    console.log(`🌐 API Base URL: ${API_BASE}`);
    
    try {
      const response = await fetch(`${API_BASE}/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        let errorData;
        try {
          errorData = await response.json();
        } catch {
          errorData = { 
            detail: `HTTP ${response.status}: ${response.statusText}` 
          };
        }
        console.error('❌ Registration failed:', errorData);
        throw new Error(errorData.detail || `Registration failed: ${response.statusText}`);
      }

      const user = await response.json();
      console.log('✅ Registration successful:', user);
      return user;
    } catch (error: any) {
      // Обработка сетевых ошибок
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        console.error('❌ Network error:', error);
        throw new Error(
          'Не удалось подключиться к API. Запустите uvicorn или проверьте REACT_APP_API_URL / proxy.'
        );
      }
      throw error;
    }
  },

  async getCurrentUser(token: string): Promise<User> {
    console.log('🔄 Getting current user data...');
    
    const response = await fetch(`${API_BASE}/users/me`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      if (response.status === 401) {
        console.warn('⚠️ Token expired or invalid');
        throw new Error('Session expired. Please login again.');
      }
      throw new Error('Failed to get user data');
    }

    const user = await response.json();
    console.log('✅ User data retrieved:', user.username);
    return user;
  },

  async getUserMinioInfo(token: string): Promise<any> {
    console.log('🔄 Getting user MinIO info...');
    
    const response = await fetch(`${API_BASE}/users/me/minio-info`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      console.warn('⚠️ Failed to get MinIO info');
      return null;
    }

    return await response.json();
  },

  isTokenExpired(token: string): boolean {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.exp * 1000 < Date.now();
    } catch {
      return true;
    }
  },

  async refreshTokens(): Promise<AuthResponse | null> {
    const rt = getRefreshTokenCookie();
    if (!rt) return null;

    try {
      const response = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: rt }),
      });

      if (!response.ok) {
        return null;
      }
      return (await response.json()) as AuthResponse;
    } catch (e) {
      console.error('❌ refreshTokens network/CORS error:', e);
      return null;
    }
  },

  async logoutRemote(refreshToken: string | null): Promise<void> {
    if (!refreshToken) return;
    try {
      await fetch(`${API_BASE}/auth/logout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
    } catch {
      /* сеть недоступна — локальная очистка всё равно выполнится */
    }
  },
};