import React from 'react';
import LoginForm from '../components/Auth/LoginForm';
import Seo from '../components/Seo';

const Login: React.FC = () => {
  return (
    <div className="login-page">
      <Seo
        title="Вход в систему"
        description="Авторизация в сервисе цензурирования изображений. Страница не индексируется."
        canonicalPath="/login"
        noindex
      />
      <LoginForm />
    </div>
  );
};

export default Login;
