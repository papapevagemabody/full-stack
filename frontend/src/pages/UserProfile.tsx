// pages/UserProfile.tsx
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { apiService, CensorshipResponse } from '../services/api';
import { usePermissions } from '../hooks/usePermissions';
import UserCatalogPanel from '../components/UserCatalogPanel';
import Seo from '../components/Seo';
import './UserProfile.css';

const UserProfile: React.FC = () => {
  const { user } = useAuth();
  const { hasPermission } = usePermissions();
  const [searchParams, setSearchParams] = useSearchParams();
  const [minioInfo, setMinioInfo] = useState<any>(null);
  const [minioLoading, setMinioLoading] = useState(true);
  const [catalogTick, setCatalogTick] = useState(0);
  const [catalogTotal, setCatalogTotal] = useState<number | null>(null);

  const activeTab = searchParams.get('tab') === 'files' ? 'files' : 'account';

  const setTab = useCallback(
    (tab: 'account' | 'files') => {
      const p = new URLSearchParams(searchParams);
      if (tab === 'files') {
        p.set('tab', 'files');
      } else {
        p.delete('tab');
      }
      setSearchParams(p, { replace: true });
    },
    [searchParams, setSearchParams]
  );

  // Кнопки вместо видимого "upload input"
  const previewFileInputRef = useRef<HTMLInputElement>(null);
  const censorFileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [censoring, setCensoring] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const selectedMethod = 'pixelate';
  const censorshipParams: Record<string, any> = { pixel_size: 15, blur_strength: 31 };

  const canUpload = hasPermission('files.upload');
  const canUseCensor = hasPermission('censor.use');

  const bumpCatalog = useCallback(() => {
    setCatalogTick((t) => t + 1);
  }, []);

  const handleCatalogMeta = useCallback((meta: { total: number }) => {
    setCatalogTotal(meta.total);
  }, []);

  useEffect(() => {
    const loadMinio = async () => {
      if (!user) {
        return;
      }
      setMinioLoading(true);
      try {
        try {
          const info = await apiService.getUserMinioInfo();
          setMinioInfo(info);
        } catch (minioError: any) {
          console.warn('⚠️ [Profile] Could not load MinIO info:', minioError);
          setMinioInfo({
            username: user.username,
            files_bucket: 'unknown',
            user_folder: 'unknown',
            storage_used: '0 B',
            provider: 'MinIO',
            error: minioError.message,
          });
        }
      } finally {
        setMinioLoading(false);
      }
    };

    void loadMinio();
  }, [user]);

  const handleRefreshFiles = () => {
    bumpCatalog();
  };

  const handlePreviewUpload = async (rawFiles: FileList | null) => {
    if (!rawFiles || rawFiles.length === 0) return;
    setActionError(null);
    setUploading(true);
    try {
      if (!user) throw new Error('Для загрузки нужно войти в систему');
      if (!canUpload) throw new Error('Нет прав на загрузку файлов');

      await apiService.uploadFiles(rawFiles);
      bumpCatalog();
    } catch (e: any) {
      setActionError(e?.message || 'Ошибка загрузки');
    } finally {
      setUploading(false);
      if (previewFileInputRef.current) previewFileInputRef.current.value = '';
    }
  };

  const handleApplyCensor = async (rawFile: File | null) => {
    if (!rawFile) return;
    setActionError(null);
    setCensoring(true);
    try {
      if (!user) throw new Error('Для цензуры нужно войти в систему');
      if (!canUseCensor) throw new Error('Нет прав на использование цензурирования');

      const resp: CensorshipResponse = await apiService.censorImage(
        rawFile,
        selectedMethod,
        censorshipParams
      );
      if (!resp?.success) {
        throw new Error(resp?.message || 'Ошибка при цензурировании');
      }
      bumpCatalog();
    } catch (e: any) {
      setActionError(e?.message || 'Ошибка при цензурировании');
    } finally {
      setCensoring(false);
      if (censorFileInputRef.current) censorFileInputRef.current.value = '';
    }
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (!user) {
    return (
      <div className="profile-container">
        <Seo
          title="Профиль — требуется вход"
          description="Личный кабинет доступен после авторизации."
          canonicalPath="/profile"
          noindex
        />
        <div className="profile-card">
          <h2>⚠️ Доступ запрещен</h2>
          <p>
            Для просмотра профиля необходимо <a href="/login">войти в систему</a>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="user-profile">
      <Seo
        title={`Профиль — ${user.username}`}
        description="Аккаунт, хранилище и история изображений с каталогом материалов."
        canonicalPath="/profile"
        noindex
      />
      <div className="profile-header">
        <h1>Профиль</h1>
      </div>

      <div className="profile-tabs">
        <button
          className={`tab-button ${activeTab === 'account' ? 'active' : ''}`}
          onClick={() => setTab('account')}
        >
          Информация аккаунта
        </button>
        <button
          className={`tab-button ${activeTab === 'files' ? 'active' : ''}`}
          onClick={() => setTab('files')}
        >
          История изображений
          {catalogTotal !== null ? ` (${catalogTotal})` : ''}
        </button>
      </div>

      {activeTab === 'account' ? (
        <div className="profile-grid">
          <div className="profile-card">
            <h2>Информация аккаунта</h2>
            <div className="info-grid">
              <div className="info-item">
                <span className="info-label">Имя пользователя:</span>
                <span className="info-value">{user.username}</span>
              </div>

              {user.email && (
                <div className="info-item">
                  <span className="info-label">Email:</span>
                  <span className="info-value">{user.email}</span>
                </div>
              )}

              {user.created_at && (
                <div className="info-item">
                  <span className="info-label">Дата регистрации:</span>
                  <span className="info-value">{formatDate(user.created_at)}</span>
                </div>
              )}

              {minioLoading ? (
                <div className="info-item">
                  <span className="info-label">Хранилище:</span>
                  <span className="info-value">Загрузка…</span>
                </div>
              ) : (
                minioInfo && (
                  <>
                    <div className="info-item">
                      <span className="info-label">Хранилище:</span>
                      <span className="info-value storage-badge">{minioInfo.provider || 'MinIO'}</span>
                    </div>

                    {minioInfo.user_folder && !minioInfo.error ? (
                      <div className="info-item">
                        <span className="info-label">Папка в MinIO:</span>
                        <span className="info-value code">{minioInfo.user_folder}</span>
                      </div>
                    ) : minioInfo.error ? (
                      <div className="info-item error">
                        <span className="info-label">Статус MinIO:</span>
                        <span className="info-value error-text" title={minioInfo.error}>
                          ⚠️ Ошибка аутентификации
                        </span>
                      </div>
                    ) : null}

                    {minioInfo.files_bucket && !minioInfo.error && (
                      <div className="info-item">
                        <span className="info-label">Бакет:</span>
                        <span className="info-value">{minioInfo.files_bucket}</span>
                      </div>
                    )}

                    {minioInfo.storage_used && !minioInfo.error && (
                      <div className="info-item">
                        <span className="info-label">Использовано:</span>
                        <span className="info-value">{minioInfo.storage_used}</span>
                      </div>
                    )}
                  </>
                )
              )}
            </div>
          </div>

          <div className="profile-card">
            <h2>Системная информация</h2>
            <div className="info-grid">
              <div className="info-item">
                <span className="info-label">Система цензурирования:</span>
                <span className="info-value">AI Face Detection</span>
              </div>

              <div className="info-item">
                <span className="info-label">Методы цензурирования:</span>
                <span className="info-value">Пикселизация</span>
              </div>

              <div className="info-item">
                <span className="info-label">Поддерживаемые форматы:</span>
                <span className="info-value">JPG, PNG</span>
              </div>

              <div className="info-item">
                <span className="info-label">Максимальный размер файла:</span>
                <span className="info-value">10 MB</span>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="files-section">
          <div className="files-header">
            <div className="header-title">
              <h2>История изображений</h2>
              <span className="files-count">
                {catalogTotal !== null ? `${catalogTotal} записей в каталоге` : 'Каталог'}
              </span>
            </div>
            <div className="header-actions">
              <button
                onClick={handleRefreshFiles}
                className="refresh-button"
                type="button"
                title="Обновить список каталога"
              >
                🔄 Обновить список
              </button>

              <button
                type="button"
                className="profile-action-button profile-action-button--preview"
                onClick={() => previewFileInputRef.current?.click()}
                disabled={uploading || !user || !canUpload}
                title={!canUpload ? 'Нет прав на загрузку файлов' : ''}
              >
                {uploading ? 'Загрузка...' : '👁️ Предварительный просмотр'}
              </button>

              <button
                type="button"
                className="profile-action-button profile-action-button--censor"
                onClick={() => censorFileInputRef.current?.click()}
                disabled={censoring || !user || !canUseCensor}
                title={!canUseCensor ? 'Нет прав на использование цензурирования' : ''}
              >
                {censoring ? 'Обработка...' : '🛡️ Применить цензуру'}
              </button>

              <input
                ref={previewFileInputRef}
                type="file"
                multiple
                accept="image/*"
                style={{ display: 'none' }}
                onChange={(e) => handlePreviewUpload(e.target.files)}
              />
              <input
                ref={censorFileInputRef}
                type="file"
                accept="image/*"
                style={{ display: 'none' }}
                onChange={(e) => handleApplyCensor(e.target.files?.[0] || null)}
              />
            </div>
          </div>

          {actionError && (
            <div className="profile-action-error" role="alert">
              {actionError}
            </div>
          )}

          <UserCatalogPanel
            hideTitle
            refreshTrigger={catalogTick}
            onMeta={handleCatalogMeta}
          />

          {minioInfo && !minioInfo.error && (
            <div className="storage-info">
              <h3>Информация о хранилище</h3>
              <div className="storage-details">
                <div className="storage-item">
                  <span className="storage-label">Провайдер:</span>
                  <span className="storage-value">{minioInfo.provider || 'MinIO'}</span>
                </div>

                {minioInfo.files_bucket && (
                  <div className="storage-item">
                    <span className="storage-label">Бакет:</span>
                    <span className="storage-value">{minioInfo.files_bucket}</span>
                  </div>
                )}

                {minioInfo.user_folder && (
                  <div className="storage-item">
                    <span className="storage-label">Папка пользователя:</span>
                    <span className="storage-value code">{minioInfo.user_folder}</span>
                  </div>
                )}

                {minioInfo.storage_used && (
                  <div className="storage-item">
                    <span className="storage-label">Использовано:</span>
                    <span className="storage-value">{minioInfo.storage_used}</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default UserProfile;
