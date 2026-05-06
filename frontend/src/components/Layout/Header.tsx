import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { usePermissions } from '../../hooks/usePermissions';

const Header: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { isAdmin } = usePermissions();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleProfileClick = () => {
    navigate('/profile');
  };

  const isActive = (path: string) => location.pathname === path;

  return (
    <div style={styles.header}>
      <div style={styles.container}>
        {/* Логотип слева - БЕЗ прямоугольника */}
        <Link to="/" style={styles.logoLink}>
          <div style={styles.logo}>
            Цензура ПД
          </div>
        </Link>

        {/* Центральная навигация - выделенные кнопки */}
        <div style={styles.centerNav}>
          <Link 
            to="/" 
            style={{
              ...styles.mainButton,
              ...(isActive('/') ? styles.activeMainButton : {})
            }}
          >
            <span style={styles.mainText}>Главная</span>
          </Link>
          
          {user && (
            <>
              <Link 
                to="/redaction" 
                style={{
                  ...styles.mainButton,
                  ...(isActive('/redaction') ? styles.activeMainButton : {})
                }}
              >
                <span style={styles.mainText}>Редактор</span>
              </Link>
              {isAdmin && (
                <Link 
                  to="/admin/users" 
                  style={{
                    ...styles.mainButton,
                    ...(isActive('/admin/users') ? styles.activeMainButton : {})
                  }}
                >
                  <span style={styles.mainText}>Управление</span>
                </Link>
              )}
            </>
          )}
        </div>

        {/* Правая часть */}
        <div style={styles.rightSection}>
          {/* Кнопка "О проекте" */}
          <Link 
            to="/about" 
            style={{
              ...styles.secondaryButton,
              ...(isActive('/about') ? styles.activeSecondaryButton : {})
            }}
          >
            <span style={styles.secondaryText}>О проекте</span>
          </Link>

          {/* Блок пользователя или кнопки авторизации */}
          {user ? (
            <div style={styles.userBlock}>
              {/* Кнопка профиля совмещена с информацией о пользователе */}
              <div 
                style={styles.userInfoButton}
                onClick={handleProfileClick}
                title="Перейти в профиль"
              >
                <span style={styles.userIcon}>{user.is_admin ? '👑' : '👤'}</span>
                <span style={styles.userName}>{user.username}</span>
                {user.is_admin && <span style={styles.adminTag}>A</span>}
              </div>
              
              {/* Только кнопка Выйти */}
              <div style={styles.userActions}>
                <button 
                  onClick={handleLogout}
                  style={styles.logoutButton}
                >
                  Выйти
                </button>
              </div>
            </div>
          ) : (
            <div style={styles.authButtons}>
              <Link 
                to="/login" 
                style={{
                  ...styles.secondaryButton,
                  ...(isActive('/login') ? styles.activeSecondaryButton : {})
                }}
              >
                <span style={styles.secondaryIcon}>🔐</span>
                <span style={styles.secondaryText}>Войти</span>
              </Link>
              <Link 
                to="/register" 
                style={{
                  ...styles.secondaryButton,
                  ...(isActive('/register') ? styles.activeSecondaryButton : {})
                }}
              >
                <span style={styles.secondaryIcon}>📝</span>
                <span style={styles.secondaryText}>Регистрация</span>
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Обновлённые стили
const styles = {
  header: {
    position: 'fixed' as 'fixed',
    top: 0,
    left: 0,
    right: 0,
    background: 'linear-gradient(135deg, #34495E 0%, #34495E 100%)',
    padding: '10px 20px',
    boxShadow: '0 4px 20px rgba(0, 0, 0, 0.25)',
    zIndex: 1000,
    borderBottom: '2px solid rgba(255, 255, 255, 0.2)',
    height: '70px',
    display: 'flex',
    alignItems: 'center',
  },
  container: {
    width: '100%',
    maxWidth: '1600px',
    margin: '0 auto',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    height: '100%',
  },
  logoLink: {
    textDecoration: 'none',
    flexShrink: 0 as 0,
  },
  logo: {
    fontSize: '1.8rem',
    fontWeight: 700,
    color: 'white',
    textShadow: '1px 1px 3px rgba(0, 0, 0, 0.3)',
    letterSpacing: '1px',
    transition: 'all 0.2s ease',
    minWidth: '180px',
    textAlign: 'center' as 'center',
    display: 'inline-block',
    padding: '8px 0',
  },
  centerNav: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    gap: '40px',
    flex: 1,
    margin: '0 30px',
  },
  mainButton: {
    textDecoration: 'none',
    padding: '10px 20px',
    fontSize: '1.2rem',
    fontWeight: 600,
    color: 'white',
    background: 'rgba(255, 255, 255, 0.15)',
    border: '2px solid rgba(255, 255, 255, 0.2)',
    borderRadius: '12px',
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    minWidth: '150px',
    justifyContent: 'center',
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
    transition: 'all 0.2s ease',
    textShadow: '1px 1px 2px rgba(0, 0, 0, 0.2)',
    letterSpacing: '0.5px',
  },
  activeMainButton: {
    background: 'rgba(255, 255, 255, 0.25)',
    borderColor: '#ffd700',
    boxShadow: '0 6px 16px rgba(0, 0, 0, 0.2), inset 0 0 8px rgba(255, 255, 255, 0.1)',
  },
  mainIcon: {
    fontSize: '1.4rem',
  },
  mainText: {
    fontSize: '1.2rem',
    fontWeight: 600,
  },
  rightSection: {
    display: 'flex',
    alignItems: 'center',
    gap: '25px',
    flexShrink: 0 as 0,
  },
  secondaryButton: {
    textDecoration: 'none',
    padding: '8px 16px',
    fontSize: '1rem',
    fontWeight: 500,
    color: 'white',
    background: 'rgba(255, 255, 255, 0.08)',
    border: '1px solid rgba(255, 255, 255, 0.12)',
    borderRadius: '10px',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    minWidth: '130px',
    justifyContent: 'center',
    transition: 'all 0.2s ease',
    textShadow: '1px 1px 2px rgba(0, 0, 0, 0.2)',
  },
  activeSecondaryButton: {
    background: 'rgba(255, 255, 255, 0.15)',
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  secondaryIcon: {
    fontSize: '1.1rem',
  },
  secondaryText: {
    fontSize: '1rem',
    fontWeight: 500,
  },
  userBlock: {
    display: 'flex',
    alignItems: 'center',
    gap: '15px',
    paddingLeft: '15px',
    borderLeft: '2px solid rgba(255, 255, 255, 0.2)',
  },
  userInfoButton: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '6px 14px',
    background: 'rgba(255, 255, 255, 0.08)',
    borderRadius: '10px',
    border: '1px solid rgba(255, 255, 255, 0.12)',
    fontSize: '1rem',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    minWidth: '120px',
    justifyContent: 'center',
  },
  userIcon: {
    fontSize: '1.2rem',
  },
  userName: {
    fontWeight: 600,
    fontSize: '1rem',
    color: 'white',
  },
  adminTag: {
    background: 'linear-gradient(45deg, #ffd700, #ffaa00)',
    color: '#000',
    padding: '2px 6px',
    borderRadius: '10px',
    fontSize: '0.7rem',
    fontWeight: 700,
    border: '1px solid rgba(255, 255, 255, 0.4)',
    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.2)',
  },
  userActions: {
    display: 'flex',
    gap: '10px',
  },
  logoutButton: {
    padding: '8px 16px',
    fontSize: '1rem',
    fontWeight: 600,
    background: 'linear-gradient(135deg, #f56565, #e53e3e)',
    color: 'white',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    borderRadius: '10px',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    minWidth: '100px',
    letterSpacing: '0.5px',
    textShadow: '1px 1px 2px rgba(0, 0, 0, 0.2)',
  },
  authButtons: {
    display: 'flex',
    gap: '12px',
  },
};

export default Header;