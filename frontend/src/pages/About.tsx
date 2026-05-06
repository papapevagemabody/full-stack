import React from 'react';
import Seo from '../components/Seo';

const About: React.FC = () => {
  return (
    <div className="about">
      <Seo
        title="О проекте — цензурирование персональных данных на изображениях"
        description="Бета-версия системы автоматического обнаружения и цензурирования персональных данных на изображениях. Цели, возможности и ограничения MVP."
        canonicalPath="/about"
      />
      <h1>О проекте</h1>
      <section className="about-content" aria-labelledby="about-summary">
        <h2 id="about-summary">Назначение</h2>
        <p>
          Это бета-версия системы для автоматического обнаружения и цензурирования персональных данных
          на изображениях.
        </p>
        <h2>Для кого</h2>
        <p>
          Учебный MVP: демонстрация загрузки, обработки, хранения и каталогизации материалов с учётом
          ролей и прав доступа.
        </p>
      </section>
    </div>
  );
};

export default About;
