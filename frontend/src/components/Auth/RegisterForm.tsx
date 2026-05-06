// RegisterForm.tsx
import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import './AuthForms.css';

const RegisterForm: React.FC = () => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [registrationStep, setRegistrationStep] = useState<'form' | 'success' | 'error'>('form');
  
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Валидация
    if (password !== confirmPassword) {
      setError('Пароли не совпадают');
      return;
    }

    if (password.length < 6) {
      setError('Пароль должен содержать минимум 6 символов');
      return;
    }

    if (username.length < 3) {
      setError('Имя пользователя должно содержать минимум 3 символа');
      return;
    }

    setIsLoading(true);

    try {
      console.log('🔄 Начало регистрации...');
      
      // Используем метод register из AuthContext
      await register({ username, email: email || undefined, password });
      
      setRegistrationStep('success');
      
      console.log('✅ Регистрация успешна!');
      
      // Автоматический редирект через 2 секунды
      setTimeout(() => {
        navigate('/');
      }, 2000);
      
    } catch (err) {
      console.error('❌ Ошибка регистрации:', err);
      setError(err instanceof Error ? err.message : 'Ошибка регистрации');
      setRegistrationStep('error');
    } finally {
      setIsLoading(false);
    }
  };

  if (registrationStep === 'success') {
    return (
      <div className="auth-container">
        <div className="auth-success">
          <div className="success-icon">🎉</div>
          <h2>Регистрация успешна!</h2>
          <p>Добро пожаловать, <strong>{username}</strong>!</p>
          <p>Ваш аккаунт успешно создан.</p>
          <p className="redirect-message">Перенаправление на главную страницу...</p>
          <button 
            onClick={() => navigate('/')}
            className="auth-button"
          >
            Перейти на главную
          </button>
        </div>
      </div>
    );
  }

  if (registrationStep === 'error') {
    return (
      <div className="auth-container">
        <div className="auth-error">
          <div className="error-icon">❌</div>
          <h2>Ошибка регистрации</h2>
          <p>{error}</p>
          <button 
            onClick={() => {
              setRegistrationStep('form');
              setError('');
            }}
            className="auth-button"
          >
            Попробовать снова
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-container">
      <form className="auth-form" onSubmit={handleSubmit}>
        <h2>Создание аккаунта</h2>
        
        {error && <div className="error-message">{error}</div>}

        <div className="form-group">
          <label htmlFor="username">Имя пользователя:*</label>
          <input
            type="text"
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            disabled={isLoading}
            placeholder="От 3 символов"
            minLength={3}
            autoComplete="username"
          />
        </div>

        <div className="form-group">
          <label htmlFor="email">Email (необязательно):</label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={isLoading}
            placeholder="your@email.com"
            autoComplete="email"
          />
        </div>

        <div className="form-group">
          <label htmlFor="password">Пароль:*</label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            disabled={isLoading}
            placeholder="Минимум 6 символов"
            minLength={6}
            autoComplete="new-password"
          />
        </div>

        <div className="form-group">
          <label htmlFor="confirmPassword">Подтвердите пароль:*</label>
          <input
            type="password"
            id="confirmPassword"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            disabled={isLoading}
            placeholder="Повторите пароль"
            autoComplete="new-password"
          />
        </div>

        <button type="submit" disabled={isLoading} className="auth-button primary">
          {isLoading ? 'Создание аккаунта...' : 'Создать аккаунт'}
        </button>

        <div className="auth-links">
          <p>Уже есть аккаунт? <a href="/login">Войти</a></p>
        </div>
      </form>
    </div>
  );
};

export default RegisterForm;