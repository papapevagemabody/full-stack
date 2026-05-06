import React from 'react';
import RedactionPrototype from '../components/RedactionPrototype/RedactionPrototype';
import Seo from '../components/Seo';

const RedactionPage: React.FC = () => {
  return (
    <div className="redaction-page">
      <Seo
        title="Редактор изображений"
        description="Рабочая область цензурирования. Доступно после входа. Не индексируется."
        canonicalPath="/redaction"
        noindex
      />
      <RedactionPrototype />
    </div>
  );
};

export default RedactionPage;