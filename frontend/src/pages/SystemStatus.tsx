// pages/SystemStatus.tsx
import React from 'react';
import MinioStatus from '../components/MinioStatus';
import Seo from '../components/Seo';

const SystemStatus: React.FC = () => {
  return (
    <div className="system-status-page">
      <Seo
        title="Системный статус"
        description="Служебная страница состояния MinIO и сервисов. Не предназначена для поисковой выдачи."
        canonicalPath="/status"
        noindex
      />
      <MinioStatus />
    </div>
  );
};

export default SystemStatus;
