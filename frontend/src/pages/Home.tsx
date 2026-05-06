// frontend/src/pages/Home.tsx
import React, { Suspense, lazy } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import Seo from '../components/Seo';
import { getPublicSiteUrl } from '../config/site';
import './Home.css';

const WeatherPanel = lazy(() => import('../components/WeatherPanel'));

const Home: React.FC = () => {
  const { user } = useAuth();
  const site = getPublicSiteUrl().replace(/\/$/, '') || '';

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: 'Система цензурирования изображений',
    url: site ? `${site}/` : '/',
    description: 'Обнаружение и скрытие лиц на изображениях с использованием AI.',
    inLanguage: 'ru-RU',
  };

  return (
    <div className="home-container">
      <Seo
        title="Система цензурирования изображений — главная"
        description="Обнаружение лиц на фото, пикселизация и безопасное хранение. Учебный MVP с MinIO и каталогом материалов."
        canonicalPath="/"
        jsonLd={jsonLd}
      />

      <div className="hero-section">
        <h1>Система цензурирования изображений</h1>
        <p>Обнаружение и скрытие лиц на изображениях с использованием AI</p>
      </div>

      <div className="features-section">
        <article className="feature-card">
          <h2>Обнаружение лиц</h2>
          <p>Автоматическое обнаружение лиц на изображениях с помощью нейросетей</p>
        </article>

        <article className="feature-card">
          <h2>Цензурирование</h2>
          <p>Размытие и скрытие обнаруженных областей для защиты приватности</p>
        </article>

        <article className="feature-card">
          <h2>Безопасное хранение</h2>
          <p>Ваши файлы безопасно хранятся в изолированных контейнерах</p>
        </article>
      </div>

      <div className="action-section">
        {user ? (
          <div className="user-actions">
            <h2>Добро пожаловать, {user.username}!</h2>
            <p>Вы можете начать работу с редактором изображений</p>
            <Link to="/redaction" className="action-button primary">
              Перейти в редактор
            </Link>
          </div>
        ) : (
          <div className="guest-actions">
            <h2>Начните работу с системой</h2>
            <p>Зарегистрируйтесь или войдите в систему для доступа к функциям</p>
            <div className="action-buttons">
              <Link to="/register" className="action-button primary">
                Зарегистрироваться
              </Link>
              <Link to="/login" className="action-button secondary">
                Войти в систему
              </Link>
            </div>
          </div>
        )}
      </div>

      <section className="info-section" aria-labelledby="how-it-works">
        <h2 id="how-it-works">Как это работает?</h2>
        <div className="steps">
          <div className="step">
            <span className="step-number">1</span>
            <p>Загрузите изображение</p>
          </div>
          <div className="step">
            <span className="step-number">2</span>
            <p>Система автоматически обнаружит лица</p>
          </div>
          <div className="step">
            <span className="step-number">3</span>
            <p>Примените цензурирование к нужным областям</p>
          </div>
          <div className="step">
            <span className="step-number">4</span>
            <p>Скачайте обработанное изображение</p>
          </div>
        </div>
      </section>

      <Suspense fallback={<p className="weather-lazy-fallback">Загрузка блока погоды…</p>}>
        <WeatherPanel />
      </Suspense>
    </div>
  );
};

export default Home;
