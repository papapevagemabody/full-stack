import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

interface MinioStatusProps {}

const MinioStatus: React.FC<MinioStatusProps> = () => {
  const [systemInfo, setSystemInfo] = useState<any>(null);
  const [userFiles, setUserFiles] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { user } = useAuth();

  useEffect(() => {
    const fetchSystemInfo = async () => {
      try {
        setLoading(true);
        const [info, filesResponse, debugInfo] = await Promise.all([
          apiService.getSystemInfo(),
          apiService.getUserFiles().catch(() => []),
          apiService.getSystemStatus().catch(() => null)
        ]);
        
        setSystemInfo({
          ...info,
          debugInfo
        });
        setUserFiles(filesResponse || []);
      } catch (error) {
        console.error('Error fetching system info:', error);
        setError('Failed to load system information');
      } finally {
        setLoading(false);
      }
    };

    fetchSystemInfo();
  }, []);

  if (loading) return <div className="loading">Загрузка информации о системе...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="system-status-page">
      <h2>Статус системы</h2>
      
      <div className="status-grid">
        {/* PostgreSQL Status */}
        <div className="status-card database">
          <h3>🗄️ PostgreSQL Database</h3>
          <div className="status-indicator online">
            <span className="dot"></span>
            Онлайн
          </div>
          <div className="status-details">
            <p><strong>Хранение:</strong> Данные пользователей</p>
            <p><strong>Пользователей в системе:</strong> {systemInfo?.debugInfo?.total_users || 'N/A'}</p>
            {user && (
              <p><strong>Текущий пользователь:</strong> {user.username}</p>
            )}
          </div>
        </div>

        {/* MinIO Status */}
        <div className="status-card storage">
          <h3>📦 MinIO Storage</h3>
          <div className={`status-indicator ${systemInfo?.debugInfo?.services?.minio ? 'online' : 'offline'}`}>
            <span className="dot"></span>
            {systemInfo?.debugInfo?.services?.minio ? 'Онлайн' : 'Оффлайн'}
          </div>
          <div className="status-details">
            <p><strong>Назначение:</strong> Хранение файлов</p>
            <p><strong>Bucket:</strong> {systemInfo?.storage?.user_files_bucket || 'user-files'}</p>
            <p><strong>Всего файлов:</strong> {systemInfo?.debugInfo?.total_files || 0}</p>
            {user?.minio_folder && (
              <p><strong>Ваша папка:</strong> {user.minio_folder}</p>
            )}
          </div>
        </div>

        {/* API Status */}
        <div className="status-card api">
          <h3>⚡ FastAPI Backend</h3>
          <div className="status-indicator online">
            <span className="dot"></span>
            Работает
          </div>
          <div className="status-details">
            <p><strong>Версия:</strong> {systemInfo?.version || '2.0.0'}</p>
            <p><strong>Аутентификация:</strong> JWT</p>
            <p><strong>Документация:</strong> <a href="/api/docs" target="_blank">/api/docs</a></p>
          </div>
        </div>
      </div>

      {/* User Files Section */}
      {userFiles.length > 0 && (
        <div className="files-section">
          <h3>📁 Ваши файлы в MinIO</h3>
          <div className="files-list">
            {userFiles.map((file, index) => (
              <div key={index} className="file-item">
                <div className="file-icon">📄</div>
                <div className="file-info">
                  <div className="file-name">{file.name || file.object_name}</div>
                  <div className="file-meta">
                    <span>Размер: {(file.size / 1024).toFixed(2)} KB</span>
                    {file.last_modified && (
                      <span>Загружен: {new Date(file.last_modified).toLocaleDateString()}</span>
                    )}
                  </div>
                </div>
                <a href={file.url} target="_blank" rel="noopener noreferrer" className="file-link">
                  Открыть
                </a>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* System Details */}
      <div className="system-details">
        <h3>🔧 Технические детали</h3>
        <div className="details-grid">
          <div className="detail-item">
            <strong>Backend:</strong> FastAPI (Python)
          </div>
          <div className="detail-item">
            <strong>Database:</strong> PostgreSQL
          </div>
          <div className="detail-item">
            <strong>File Storage:</strong> MinIO (S3 совместимый)
          </div>
          <div className="detail-item">
            <strong>Frontend:</strong> React + TypeScript
          </div>
          <div className="detail-item">
            <strong>Auth:</strong> JWT + SHA256 хеширование
          </div>
          <div className="detail-item">
            <strong>API URL:</strong> http://localhost:8001
          </div>
        </div>
      </div>

      {systemInfo?.debugInfo && (
        <div className="debug-info">
          <button 
            onClick={() => {
              console.log('Debug Info:', systemInfo.debugInfo);
              alert('Debug информация выведена в консоль');
            }}
            className="debug-button"
          >
            Показать отладочную информацию
          </button>
        </div>
      )}
    </div>
  );
};

export default MinioStatus;