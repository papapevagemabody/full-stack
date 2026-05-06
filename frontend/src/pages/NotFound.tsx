import React from 'react';
import { Link } from 'react-router-dom';
import Seo from '../components/Seo';

const NotFound: React.FC = () => {
  return (
    <div className="not-found">
      <Seo
        title="Страница не найдена (404)"
        description="Запрошенный адрес не существует в приложении."
        noindex
      />
      <h1>404 — страница не найдена</h1>
      <p>Извините, запрашиваемая страница не существует.</p>
      <Link to="/" className="back-home">
        Вернуться на главную
      </Link>
    </div>
  );
};

export default NotFound;
