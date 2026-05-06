// AuthContext.tsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, AuthContextType, RegisterData } from '../types/auth';
import { authService } from '../services/authService';
import { apiService } from '../services/api';
import {
  migrateTokensFromLocalStorage,
  getAccessTokenCookie,
  getRefreshTokenCookie,
  setAccessTokenCookie,
  setRefreshTokenCookie,
} from '../utils/authCookies';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(() => {
    migrateTokensFromLocalStorage();
    return getAccessTokenCookie();
  });
  const [isLoading, setIsLoading] = useState(true);
  const [userMinioInfo, setUserMinioInfo] = useState<any>(null);

  useEffect(() => {
    const offAccess = apiService.subscribeAccessToken((t) => setToken(t));
    const offInvalid = apiService.subscribeSessionInvalid(() => {
      setUser(null);
      setToken(null);
      setUserMinioInfo(null);
      localStorage.removeItem('user');
    });
    return () => {
      offAccess();
      offInvalid();
    };
  }, []);

  useEffect(() => {
    const initAuth = async () => {
      migrateTokensFromLocalStorage();
      let access = getAccessTokenCookie();
      const refresh = getRefreshTokenCookie();

      if (access && authService.isTokenExpired(access) && refresh) {
        try {
          const tokens = await authService.refreshTokens();
          if (tokens) {
            access = tokens.access_token;
            setAccessTokenCookie(tokens.access_token);
            if (tokens.refresh_token) {
              setRefreshTokenCookie(tokens.refresh_token);
            }
            apiService.setToken(tokens.access_token);
          } else {
            apiService.clearToken();
            setToken(null);
            setUser(null);
            localStorage.removeItem('user');
            setIsLoading(false);
            return;
          }
        } catch (e) {
          // Любая ошибка refresh (включая сеть/CORS) => корректно завершаем с очисткой.
          console.error('❌ Failed to refresh on init:', e);
          apiService.clearToken();
          setToken(null);
          setUser(null);
          localStorage.removeItem('user');
          setIsLoading(false);
          return;
        }
      } else if (access && authService.isTokenExpired(access)) {
        apiService.clearToken();
        setToken(null);
        setUser(null);
        localStorage.removeItem('user');
        setIsLoading(false);
        return;
      }

      if (access) {
        try {
          console.log('🔄 Initializing auth from stored token...');
          apiService.setToken(access);
          let userData: User;
          try {
            userData = await authService.getCurrentUser(access);
          } catch {
            if (refresh) {
              const tokens = await authService.refreshTokens();
              if (!tokens) {
                throw new Error('refresh failed');
              }
              access = tokens.access_token;
              setAccessTokenCookie(tokens.access_token);
              if (tokens.refresh_token) {
                setRefreshTokenCookie(tokens.refresh_token);
              }
              apiService.setToken(tokens.access_token);
              setToken(tokens.access_token);
              userData = await authService.getCurrentUser(tokens.access_token);
            } else {
              throw new Error('no refresh');
            }
          }
          setUser(userData);
          localStorage.setItem('user', JSON.stringify(userData));

          try {
            const minioInfo = await authService.getUserMinioInfo(access!);
            setUserMinioInfo(minioInfo);
          } catch (minioError) {
            console.warn('⚠️ Could not fetch MinIO info:', minioError);
          }

          console.log('✅ User authenticated:', userData.username);
        } catch (error) {
          console.error('❌ Failed to get user data:', error);
          apiService.clearToken();
          setToken(null);
          setUser(null);
          localStorage.removeItem('user');
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, []);

  const login = async (username: string, password: string): Promise<User> => {
    setIsLoading(true);
    try {
      console.log(`🔄 Login attempt for: ${username}`);
      
      const authResponse = await authService.login(username, password);
      const { access_token, refresh_token } = authResponse;
      
      console.log('✅ Tokens received, storing...');
      
      setToken(access_token);
      setAccessTokenCookie(access_token);
      setRefreshTokenCookie(refresh_token);
      apiService.setToken(access_token);
      
      console.log('🔄 Getting user data...');
      const userData = await authService.getCurrentUser(access_token);
      setUser(userData);
      localStorage.setItem('user', JSON.stringify(userData));
      
      // Не блокируем успешный логин на дополнительном запросе MinIO.
      // Даже если MinIO недоступен/медленный, пользователь должен сразу попасть в приложение.
      void authService
        .getUserMinioInfo(access_token)
        .then((minioInfo) => setUserMinioInfo(minioInfo))
        .catch((minioError) => {
          console.warn('⚠️ Could not fetch MinIO info:', minioError);
        });
      
      console.log('🎉 Login successful:', userData.username);
      return userData;
    } catch (error) {
      console.error('❌ Login failed:', error);
      clearLocalAuth();
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (data: RegisterData): Promise<User> => {
    setIsLoading(true);
    try {
      console.log(`🔄 Registration attempt for: ${data.username}`);
      
      const userData = await authService.register(data);
      
      // После регистрации автоматически логиним пользователя
      console.log('🔄 Auto-login after registration...');
      await login(data.username, data.password);
      
      console.log('🎉 Registration and login successful');
      return userData;
    } catch (error) {
      console.error('❌ Registration failed:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const clearLocalAuth = () => {
    setUser(null);
    setToken(null);
    setUserMinioInfo(null);
    apiService.clearToken();
    localStorage.removeItem('user');
  };

  const updateUser = async (updatedUser: Partial<User>): Promise<void> => {
    try {
      console.log('🔄 Updating user data...');
      // Здесь можно добавить вызов API для обновления данных пользователя
      setUser(prev => prev ? { ...prev, ...updatedUser } : null);
    } catch (error) {
      console.error('❌ Failed to update user:', error);
      throw error;
    }
  };

  const handleLogout = async () => {
    console.log('👋 Logging out...');
    const rt = getRefreshTokenCookie();
    await authService.logoutRemote(rt);
    clearLocalAuth();
  };

  const logout = () => {
    void handleLogout();
    console.log('✅ User logged out');
  };

  const value: AuthContextType = {
    user,
    token,
    login,
    logout,
    isLoading,
    register,
    updateUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};