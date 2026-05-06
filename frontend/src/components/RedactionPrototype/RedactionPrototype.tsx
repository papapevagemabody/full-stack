// components/RedactionPrototype/RedactionPrototype.tsx - дополненный
import React, { useState, useRef, useEffect } from "react";
import "../RedactionPrototype.css";
import { 
  apiService, 
  UploadResponse, 
  FileInfo, 
  CensorshipResponse,
  CensorshipMethod,
  MinioInfo,
  Detection
} from "../../services/api";
import { useAuth } from "../../contexts/AuthContext";
import { usePermissions } from "../../hooks/usePermissions";

interface FileData {
  id: string;
  name: string;
  url: string;
  detections: Detection[];
  redactions: any[];
  object_name?: string;
}

export default function RedactionPrototype() {
  const [files, setFiles] = useState<FileData[]>([]);
  const [selected, setSelected] = useState<FileData | null>(null);
  const [loading, setLoading] = useState(false);
  const [censoring, setCensoring] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [userFiles, setUserFiles] = useState<FileInfo[]>([]);
  const [minioInfo, setMinioInfo] = useState<MinioInfo | null>(null);
  const [censorshipMethods, setCensorshipMethods] = useState<CensorshipMethod[]>([]);
  const [selectedMethod, setSelectedMethod] = useState<string>('pixelate');
  const [censorshipParams, setCensorshipParams] = useState<Record<string, any>>({
    pixel_size: 15,
    blur_strength: 31
  });
  
  const { user } = useAuth();
  const { hasPermission } = usePermissions();
  const fileInput = useRef<HTMLInputElement>(null);
  const censorFileInput = useRef<HTMLInputElement>(null);
  
  const canUpload = hasPermission('files.upload');
  const canDelete = hasPermission('files.delete_own');
  const canUseCensor = hasPermission('censor.use');

  useEffect(() => {
    if (user) {
      loadUserFiles();
      loadCensorshipMethods();
      loadMinioInfo();
    }
  }, [user]);

  const loadUserFiles = async () => {
    try {
      const files = await apiService.getUserFiles();
      setUserFiles(files);
    } catch (error) {
      console.error('Error loading user files:', error);
      setUserFiles([]);
    }
  };

  const loadCensorshipMethods = async () => {
    try {
      const methods = await apiService.getCensorshipMethods();
      setCensorshipMethods(methods);
      if (methods.length > 0) {
        setSelectedMethod(methods[0].id);
      }
    } catch (error) {
      console.error('Error loading censorship methods:', error);
      setCensorshipMethods([]);
    }
  };

  const loadMinioInfo = async () => {
    try {
      const info = await apiService.getUserMinioInfo();
      setMinioInfo(info);
    } catch (error) {
      console.error('Error loading MinIO info:', error);
      setMinioInfo(null);
    }
  };

  async function handleFiles(rawFiles: FileList | null) {
    if (!rawFiles) return;

    setLoading(true);
    setError(null);

    try {
      console.log(`🔄 Uploading ${rawFiles.length} file(s)...`);
      
      const uploadResponses: UploadResponse[] = await apiService.uploadFiles(rawFiles);
      
      const newFiles: FileData[] = uploadResponses.map(response => {
        // Нормализуем URL
        let imageUrl = response.url;
        if (!imageUrl.startsWith('http')) {
          // Если URL относительный, добавляем базовый URL
          if (imageUrl.startsWith('/')) {
            imageUrl = `http://localhost:8001${imageUrl}`;
          } else {
            imageUrl = `http://localhost:8001/${imageUrl}`;
          }
        }
        console.log('📸 Image URL:', imageUrl);
        return {
          id: response.id,
          name: response.name,
          url: imageUrl,
          detections: response.detections || [],
          redactions: response.redactions || [],
          object_name: response.object_name
        };
      });

      setFiles(prev => [...newFiles, ...prev]);
      if (!selected) setSelected(newFiles[0]);
      
      await loadUserFiles();
      
      console.log(`✅ Upload successful: ${newFiles.length} file(s) uploaded`);
    } catch (error) {
      console.error('❌ Error uploading files:', error);
      setError(error instanceof Error ? error.message : 'Ошибка при загрузке файлов');
    } finally {
      setLoading(false);
    }
  }

  async function handleCensorFile(rawFile: File | null) {
    if (!rawFile) return;

    setCensoring(true);
    setError(null);

    try {
      console.log(`🎭 Applying censorship: ${selectedMethod}...`);
      
      const response: CensorshipResponse = await apiService.censorImage(
        rawFile, 
        selectedMethod, 
        censorshipParams
      );
      
      if (response.success) {
        // Добавляем обработанный файл в список
        const newFile: FileData = {
          id: response.object_name,
          name: response.processed_filename,
          url: response.url,
          detections: [], // У цензурированного файла детекции скрыты
          redactions: [],
          object_name: response.object_name
        };

        setFiles(prev => [newFile, ...prev]);
        setSelected(newFile);
        
        await loadUserFiles();
        
        console.log(`✅ Censorship successful: ${response.message}`);
      } else {
        throw new Error(response.message);
      }
    } catch (error) {
      console.error('❌ Error applying censorship:', error);
      setError(error instanceof Error ? error.message : 'Ошибка при цензурировании');
    } finally {
      setCensoring(false);
    }
  }

  const handleFileDelete = async (fileId: string, objectName?: string) => {
    if (!window.confirm('Вы уверены, что хотите удалить этот файл?')) return;

    try {
      if (objectName) {
        await apiService.deleteFile(objectName);
      }
      
      setFiles(prev => prev.filter(f => f.id !== fileId));
      if (selected?.id === fileId) {
        setSelected(files.length > 1 ? files[1] : null);
      }
      
      await loadUserFiles();
      
      console.log('✅ File deleted');
    } catch (error) {
      console.error('❌ Error deleting file:', error);
      setError('Ошибка при удалении файла');
    }
  };

  const handleDownload = async (file: FileData) => {
    try {
      await apiService.downloadFile(file.url, file.name);
      console.log('✅ File downloaded');
    } catch (error) {
      console.error('❌ Error downloading file:', error);
      setError('Ошибка при скачивании файла');
    }
  };

  const handleParamChange = (paramName: string, value: any) => {
    setCensorshipParams(prev => ({
      ...prev,
      [paramName]: value
    }));
  };

  const getCurrentMethod = () => {
    return censorshipMethods.find(m => m.id === selectedMethod);
  };

  return (
    <div className="redaction-container">
      <div className="redaction-header">
        <h1 className="redaction-title">🎭 Цензура персональных данных</h1>
        <div className="user-info-badge">
 
        </div>
      </div>

      <div className="system-info-card">
        <div className="info-item">
          <strong>👤 Пользователь:</strong> {user?.username || 'Не авторизован'}
        </div>
        <div className="info-item">
          <strong>💾 Хранилище:</strong> {minioInfo ? 'MinIO' : 'Локальное'}
        </div>
        <div className="info-item">
          <strong>📁 Файлов:</strong> {userFiles.length}
        </div>
      </div>

      <div className="upload-section">
        <div className="upload-controls">
          <button
            onClick={() => fileInput.current?.click()}
            className="upload-button"
            disabled={loading || !user || !canUpload}
            title={!canUpload ? 'Нет прав на загрузку файлов' : ''}
          >
            {loading ? 'Загрузка...' : 'Предварительный просмотр'}
          </button>
          
          <button
            onClick={() => censorFileInput.current?.click()}
            className="censorship-button"
            disabled={censoring || !user || !canUseCensor}
            title={!canUseCensor ? 'Нет прав на использование цензурирования' : ''}
          >
            {censoring ? 'Обработка...' : 'Применить цензуру'}
          </button>
          <input
            type="file"
            ref={censorFileInput}
            className="file-input"
            onChange={e => handleCensorFile(e.target.files?.[0] || null)}
            accept="image/*"
            disabled={!user}
          />
        </div>
        
        <input
          type="file"
          ref={fileInput}
          multiple
          className="file-input"
          onChange={e => handleFiles(e.target.files)}
          accept="image/*"
          disabled={!user}
        />
        
        {!user && (
          <div className="auth-warning">
            ⚠️ Для загрузки файлов необходимо <a href="/login">войти в систему</a>
          </div>
        )}
        
        {error && (
          <div className="error-message">
            ❌ {error}
          </div>
        )}
      </div>

      {userFiles.length > 0 && (
        <div className="user-files-section">
          <h3>📁 Ваши файлы ({userFiles.length})</h3>
          <div className="files-grid">
            {userFiles.map((file, index) => (
              <div key={index} className="file-card">
                <div className="file-preview">
                  {file.name?.match(/\.(jpg|jpeg|png|gif)$/i) ? (
                    <img 
                      src={file.url} 
                      alt={file.name ? `Миниатюра: ${file.name}` : 'Загруженное изображение пользователя'} 
                      className="file-thumbnail"
                      loading="lazy"
                      decoding="async"
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = '/placeholder-image.png';
                      }}
                    />
                  ) : (
                    <div className="file-icon">📄</div>
                  )}
                </div>
                <div className="file-info">
                  <div className="file-name">{file.name || file.object_name}</div>
                  <div className="file-size">
                    {file.size ? `${(file.size / 1024).toFixed(2)} KB` : 'Unknown size'}
                  </div>
                </div>
                <div className="file-actions">
                  {file.url && (
                    <a 
                      href={file.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="action-button view"
                      title="Просмотреть"
                    >
                      👁️
                    </a>
                  )}
                  <button 
                    onClick={() => handleDownload({
                      id: index.toString(),
                      name: file.name || file.object_name || 'file',
                      url: file.url,
                      detections: [],
                      redactions: []
                    })}
                    className="action-button download"
                    title="Скачать"
                  >
                    ⬇️
                  </button>
                  {canDelete && file.object_name && (
                    <button 
                      onClick={() => handleFileDelete(index.toString(), file.object_name)}
                      className="action-button delete"
                      title="Удалить"
                    >
                      🗑️
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {files.length > 0 && (
        <div className="gallery-section">
          <h3>🖼️ Обработанные изображения ({files.length})</h3>
          <div className="gallery">
            {files.map(f => (
              <div 
                key={f.id} 
                className={`gallery-item ${selected?.id === f.id ? "selected" : ""}`}
              >
                <div onClick={() => setSelected(f)} style={{ cursor: 'pointer' }}>
                  <img
                    src={f.url}
                    alt={f.name ? `Обработанное изображение: ${f.name}` : 'Обработанное изображение'}
                    className="gallery-img"
                    loading="lazy"
                    decoding="async"
                  />
                  <div className="image-info">
                    <span className="image-name">{f.name}</span>
                    <span className="detections-count">
                      {f.detections.length > 0 ? `${f.detections.length} лиц` : 'Цензурировано'}
                    </span>
                  </div>
                </div>
                {canDelete && f.object_name && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleFileDelete(f.id, f.object_name);
                    }}
                    className="delete-gallery-item"
                    title="Удалить"
                  >
                    🗑️
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {selected && (
        <div className="viewer-section">
          <h3>🔍 Просмотр: {selected.name}</h3>
          <div className="viewer-container">
            <img
              src={selected.url}
              alt={selected.name ? `Просмотр: ${selected.name}` : 'Просмотр изображения'}
              className="viewer-img"
              loading="lazy"
              decoding="async"
              onError={(e) => {
                console.error('❌ Error loading image:', selected.url);
                const target = e.target as HTMLImageElement;
                const container = target.parentElement;
                if (container) {
                  target.style.display = 'none';
                  const errorDiv = document.createElement('div');
                  errorDiv.className = 'image-error';
                  errorDiv.innerHTML = `
                    <p>⚠️ Не удалось загрузить изображение</p>
                    <p style="font-size: 12px; color: #666; word-break: break-all;">URL: ${selected.url}</p>
                    <button onclick="window.open('${selected.url}', '_blank')">Открыть в новой вкладке</button>
                  `;
                  container.appendChild(errorDiv);
                }
              }}
              onLoad={() => {
                console.log('✅ Image loaded successfully:', selected.url);
              }}
              style={{ maxWidth: '100%', height: 'auto' }}
            />
            {selected.detections.map((d, i) => {
              const [x, y, w, h] = d.bbox;
              return (
                <div
                  key={i}
                  className="detection-box"
                  style={{
                    left: `${x * 100}%`,
                    top: `${y * 100}%`,
                    width: `${w * 100}%`,
                    height: `${h * 100}%`
                  }}
                >
                  <span className="detection-label">👤 {d.type}</span>
                </div>
              );
            })}
          </div>
          <div className="detection-info">
            <h4>Обнаружено: {selected.detections.length} лиц</h4>
            <div className="detection-controls">
              <button 
                className="control-button download-btn"
                onClick={() => handleDownload(selected)}
              >
                ⬇️ Скачать оригинал
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="system-status">
        <h3>📊 Статус системы</h3>
        <div className="status-items">
          <div className={`status-item ${user ? 'success' : 'warning'}`}>
            <span className="status-icon">{user ? '✅' : '⚠️'}</span>
            Пользователь: {user ? user.username : 'Не авторизован'}
          </div>
          <div className={`status-item ${minioInfo ? 'success' : 'warning'}`}>
            <span className="status-icon">{minioInfo ? '✅' : '⚠️'}</span>
            Хранилище: {minioInfo ? 'MinIO' : 'Локальное'}
          </div>
          <div className="status-item success">
            <span className="status-icon">✅</span>
            API: Работает
          </div>
        </div>
      </div>
    </div>
  );
}