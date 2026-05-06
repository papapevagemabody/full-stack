// Register.tsx
import React from 'react';
import RegisterForm from '../components/Auth/RegisterForm';
import Seo from '../components/Seo';

const Register: React.FC = () => {
  return (
    <div className="register-page">
      <Seo
        title="Регистрация"
        description="Создание учётной записи. Страница не индексируется поисковыми системами."
        canonicalPath="/register"
        noindex
      />
      <RegisterForm />
    </div>
  );
};

export default Register;
