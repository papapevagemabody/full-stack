// services/api.ts - дополненный
import { authService } from './authService';
import {
  getAccessTokenCookie,
  getRefreshTokenCookie,
  setAccessTokenCookie,
  setRefreshTokenCookie,
  clearAccessTokenCookie,
  clearAuthCookies,
} from '../utils/authCookies';
import { getApiBase } from '../config/apiBase';

const API_DEFAULT = getApiBase();

export interface Detection {
  type: string;
  bbox: [number, number, number, number];
  confidence?: number;
}

export interface FileInfo {
  id?: string;
  name: string;
  url: string;
  size?: number;
  object_name?: string;
  detections?: Detection[];
  last_modified?: string;
  type?: string;
}

export interface UploadResponse {
  id: string;
  name: string;
  url: string;
  detections: Detection[];
  redactions: any[];
  object_name?: string;
}

export interface CensorshipRequest {
  pixel_size?: number;
  blur_strength?: number;
  method?: 'pixelate' | 'blur' | 'black_bar';
}

export interface CensorshipResponse {
  success: boolean;
  message: string;
  original_filename: string;
  processed_filename: string;
  object_name: string;
  url: string;
  censorship_method: string;
  pixel_size?: number;
  blur_strength?: number;
}

export interface CensorshipMethod {
  id: string;
  name: string;
  description: string;
  parameters: {
    name: string;
    type: string;
    min: number;
    max: number;
    default: number;
    description: string;
  }[];
}

/** Лаб. №4: ответ backend /public/weather (Open-Meteo) */
export interface PublicWeatherPayload {
  available: boolean;
  city: string;
  country?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  temperature_c?: number | null;
  wind_speed_kmh?: number | null;
  weather_code?: number | null;
  provider?: string;
  message?: string | null;
}

export interface MinioInfo {
  username: string;
  minio_access_key?: string;
  files_bucket: string;
  user_folder: string;
  storage_used: string;
  total_files?: number;
  bucket?: string;
  folder?: string;
  provider?: string;
  error?: string;
}

class ApiService {
  private baseUrl = API_DEFAULT;
  private token: string | null = null;
  private refreshInFlight: Promise<boolean> | null = null;
  private accessTokenListeners: Array<(token: string) => void> = [];
  private sessionInvalidListeners: Array<() => void> = [];

  subscribeAccessToken(cb: (token: string) => void): () => void {
    this.accessTokenListeners.push(cb);
    return () => {
      this.accessTokenListeners = this.accessTokenListeners.filter((x) => x !== cb);
    };
  }

  subscribeSessionInvalid(cb: () => void): () => void {
    this.sessionInvalidListeners.push(cb);
    return () => {
      this.sessionInvalidListeners = this.sessionInvalidListeners.filter((x) => x !== cb);
    };
  }

  private notifyAccessTokenUpdated(token: string) {
    this.accessTokenListeners.forEach((cb) => cb(token));
  }

  private notifySessionInvalid() {
    this.sessionInvalidListeners.forEach((cb) => cb());
  }

  private async tryRefreshAccessToken(): Promise<boolean> {
    if (this.refreshInFlight) {
      return this.refreshInFlight;
    }
    if (!getRefreshTokenCookie()) {
      return false;
    }
    this.refreshInFlight = (async () => {
      try {
        const result = await authService.refreshTokens();
        if (!result) {
          this.clearToken();
          this.notifySessionInvalid();
          return false;
        }
        this.setToken(result.access_token);
        if (result.refresh_token) {
          setRefreshTokenCookie(result.refresh_token);
        }
        this.notifyAccessTokenUpdated(result.access_token);
        return true;
      } catch {
        this.clearToken();
        this.notifySessionInvalid();
        return false;
      } finally {
        this.refreshInFlight = null;
      }
    })();
    return this.refreshInFlight;
  }

  /**
   * Запрос с Bearer; при 401 один раз пытается обновить access через refresh.
   */
  private async authorizedFetch(
    path: string,
    init: RequestInit = {},
    opts: { multipart?: boolean; _retried?: boolean } = {}
  ): Promise<Response> {
    const url = path.startsWith('http') ? path : `${this.baseUrl}${path}`;
    const buildInit = (): RequestInit => {
      const base = opts.multipart ? this.getHeadersWithoutContentType() : this.getHeaders();
      return {
        ...init,
        headers: { ...(base as Record<string, string>), ...(init.headers as Record<string, string>) },
      };
    };
    let res = await fetch(url, buildInit());
    if (res.status === 401 && !opts._retried && getRefreshTokenCookie()) {
      const ok = await this.tryRefreshAccessToken();
      if (ok) {
        return this.authorizedFetch(path, init, { ...opts, _retried: true });
      }
    }
    return res;
  }

  setToken(token: string) {
    if (token) {
      this.token = token;
      setAccessTokenCookie(token);
    } else {
      this.token = null;
      clearAccessTokenCookie();
    }
  }

  private getHeaders(): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    
    // Токен из cookie, если не задан в памяти
    let token = this.token;
    if (!token) {
      token = getAccessTokenCookie();
    }
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    console.log('🔑 [API] Headers with token:', token ? 'Yes' : 'No');
    return headers;
  }

  private getHeadersWithoutContentType(): HeadersInit {
    const headers: HeadersInit = {};
    
    // Токен из cookie, если не задан в памяти
    let token = this.token;
    if (!token) {
      token = getAccessTokenCookie();
    }
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    return headers;
  }

  async validateToken(): Promise<boolean> {
    try {
      console.log('🔑 [API] Validating token...');
      const response = await this.authorizedFetch('/users/me', { method: 'GET' });
      console.log(`🔑 [API] Token validation response: ${response.status}`);
      return response.ok;
    } catch (error) {
      console.error('🔑 [API] Token validation error:', error);
      return false;
    }
  }

  async uploadFiles(files: FileList): Promise<UploadResponse[]> {
    const formData = new FormData();
    Array.from(files).forEach(file => {
      formData.append('files', file);
    });

    const response = await this.authorizedFetch('/upload-multiple', {
      method: 'POST',
      body: formData,
    }, { multipart: true });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }

    return await response.json();
  }

  async getUserFiles(): Promise<FileInfo[]> {
    console.log('🔄 [API] Fetching user files from /files endpoint...');
    
    try {
      const response = await this.authorizedFetch('/files', { method: 'GET' });

      console.log(`📊 [API] Response status: ${response.status} ${response.statusText}`);

      if (!response.ok) {
        const errorText = await response.text();
        console.error(`❌ [API] Error response:`, errorText);
        throw new Error(`Failed to fetch user files: ${response.status} ${response.statusText} - ${errorText}`);
      }

      const responseData = await response.json();
      console.log(`✅ [API] Raw response data:`, responseData);
      
      // Обработка разных форматов ответа
      let files: any[] = [];
      
      if (Array.isArray(responseData)) {
        // Если ответ - массив файлов
        files = responseData;
        console.log(`✅ [API] Got array with ${files.length} files`);
      } else if (responseData.files && Array.isArray(responseData.files)) {
        // Если ответ {files: [...]}
        files = responseData.files;
        console.log(`✅ [API] Got files array in 'files' property: ${files.length} files`);
      } else if (responseData.items && Array.isArray(responseData.items)) {
        // Если ответ {items: [...]}
        files = responseData.items;
        console.log(`✅ [API] Got files array in 'items' property: ${files.length} files`);
      } else if (responseData.data && Array.isArray(responseData.data)) {
        // Если ответ {data: [...]}
        files = responseData.data;
        console.log(`✅ [API] Got files array in 'data' property: ${files.length} files`);
      } else {
        console.warn(`⚠️ [API] Unknown response format:`, responseData);
        // Возвращаем пустой массив
        files = [];
      }

      // Нормализуем файлы
      const normalizedFiles = files.map((file: any) => this.normalizeFileInfo(file));
      console.log(`🔄 [API] Normalized ${normalizedFiles.length} files`);
      
      return normalizedFiles;
    } catch (error) {
      console.error('❌ [API] Exception in getUserFiles:', error);
      throw error;
    }
  }

  private normalizeFileInfo(file: any): FileInfo {
    console.log(`🔄 [API] Normalizing file:`, file);
    
    // Проверяем структуру файла
    const normalized: FileInfo = {
      name: file.name || file.filename || file.object_name || 'unnamed-file',
      url: this.normalizeFileUrl(file.url || file.download_url || file.object_name || file.name),
    };

    // Добавляем дополнительные поля если они есть
    if (file.size !== undefined) normalized.size = file.size;
    if (file.object_name !== undefined) normalized.object_name = file.object_name;
    if (file.id !== undefined) normalized.id = file.id;
    if (file.detections !== undefined) normalized.detections = file.detections;
    if (file.last_modified !== undefined) normalized.last_modified = file.last_modified;
    if (file.type !== undefined) normalized.type = file.type;
    if (file.created_at !== undefined) normalized.last_modified = file.created_at;

    console.log(`✅ [API] Normalized to:`, normalized);
    return normalized;
  }

  private normalizeFileUrl(urlOrName: string): string {
    if (!urlOrName) {
      console.warn('⚠️ [API] Empty URL provided for file');
      return '';
    }

    console.log(`🔄 [API] Normalizing URL: "${urlOrName}"`);

    // Если уже полный URL
    if (urlOrName.startsWith('http://') || urlOrName.startsWith('https://')) {
      console.log(`✅ [API] Already full URL: ${urlOrName}`);
      return urlOrName;
    }

    // Если это object_name из MinIO
    if (urlOrName.includes('/') || urlOrName.includes('.')) {
      // Для MinIO файлов обычно используется формат: /files/{object_name}
      const normalizedUrl = `${this.baseUrl}/files/${encodeURIComponent(urlOrName)}`;
      console.log(`🔄 [API] Constructed MinIO URL: ${normalizedUrl}`);
      return normalizedUrl;
    }

    // Если просто имя файла
    const normalizedUrl = `${this.baseUrl}/files/${urlOrName}`;
    console.log(`🔄 [API] Constructed simple URL: ${normalizedUrl}`);
    return normalizedUrl;
  }

  async debugEndpoints(): Promise<void> {
    console.log('🔍 [API] Debugging endpoints...');
    
    const endpoints = [
      '/files',
      '/user/files',
      '/minio/files',
      '/storage/files',
      '/users/me/files'
    ];

    for (const endpoint of endpoints) {
      try {
        console.log(`🔄 [API] Testing endpoint: ${endpoint}`);
        const response = await fetch(`${this.baseUrl}${endpoint}`, {
          headers: this.getHeaders(),
        });
        console.log(`📊 [API] ${endpoint}: ${response.status} ${response.statusText}`);
        
        if (response.ok) {
          const data = await response.json();
          console.log(`✅ [API] ${endpoint} returned:`, data);
        } else {
          const errorText = await response.text();
          console.log(`❌ [API] ${endpoint} error:`, errorText);
        }
      } catch (error) {
        console.error(`💥 [API] ${endpoint} exception:`, error);
      }
    }
  }

  async testFilesEndpoint(): Promise<void> {
    console.log('🧪 [API] Testing /files endpoint...');
    
    try {
      const response = await fetch(`${this.baseUrl}/files`, {
        headers: this.getHeaders(),
      });
      
      console.log(`📊 [API] /files response: ${response.status} ${response.statusText}`);
      
      if (response.ok) {
        const contentType = response.headers.get('content-type');
        console.log(`📋 [API] Content-Type: ${contentType}`);
        
        const text = await response.text();
        console.log(`📄 [API] Response body (first 500 chars):`, text.substring(0, 500));
        
        try {
          const json = JSON.parse(text);
          console.log(`📊 [API] Parsed JSON:`, json);
          
          // Проверяем структуру
          console.log(`🔍 [API] Response type:`, typeof json);
          console.log(`🔍 [API] Is array:`, Array.isArray(json));
          if (typeof json === 'object' && json !== null) {
            console.log(`🔍 [API] Object keys:`, Object.keys(json));
          }
        } catch (parseError) {
          console.error(`❌ [API] Failed to parse JSON:`, parseError);
        }
      } else {
        const errorText = await response.text();
        console.error(`❌ [API] Error:`, errorText);
      }
    } catch (error) {
      console.error(`💥 [API] Exception:`, error);
    }
  }

  async getUserFilesAlternative(): Promise<FileInfo[]> {
    console.log('🔄 [API] Trying alternative method to get files...');
    
    try {
      // Метод 1: Через список объектов MinIO
      const minioInfo = await this.getUserMinioInfo();
      console.log(`📦 [API] MinIO info for alt method:`, minioInfo);
      
      if (minioInfo && minioInfo.user_folder) {
        // Попробуем получить файлы через другой endpoint
        try {
          const response = await this.authorizedFetch(`/minio/list/${minioInfo.user_folder}`, {
            method: 'GET',
          });
          
          if (response.ok) {
            const data = await response.json();
            console.log(`✅ [API] Got files via minio/list:`, data);
            
            if (Array.isArray(data)) {
              return data.map((item: any) => ({
                name: item.name || item.object_name,
                url: `${this.baseUrl}/minio/download/${minioInfo.user_folder}/${item.object_name}`,
                size: item.size,
                object_name: item.object_name,
                last_modified: item.last_modified
              }));
            }
          }
        } catch (minioError) {
          console.log('⚠️ [API] MinIO list endpoint failed, trying next method');
        }
      }
      
      // Метод 2: Через статус системы
      try {
        const systemInfo = await this.getSystemInfo();
        console.log(`⚙️ [API] System info:`, systemInfo);
        
        // Если в статусе системы есть информация о файлах
        if (systemInfo && systemInfo.storage && systemInfo.storage.user_files) {
          return systemInfo.storage.user_files.map((file: any) => ({
            name: file.name,
            url: file.url,
            size: file.size,
            object_name: file.object_name
          }));
        }
      } catch (systemError) {
        console.log('⚠️ [API] System info endpoint failed');
      }
      
      // Если ничего не получилось, возвращаем пустой массив
      return [];
      
    } catch (error) {
      console.error('❌ [API] Error in alternative method:', error);
      return [];
    }
  }

  async deleteFile(objectName: string): Promise<void> {
    // Кодируем object_name для URL (особенно важно для путей с слэшами)
    const encodedName = encodeURIComponent(objectName);
    const response = await this.authorizedFetch(`/files/${encodedName}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Delete failed: ${response.statusText} - ${errorText}`);
    }
  }

  async minioHealthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/health`);
      if (response.ok) {
        const data = await response.json();
        return data.minio_connected === true;
      }
      return false;
    } catch {
      return false;
    }
  }

  async getCensorshipMethods(): Promise<CensorshipMethod[]> {
    const response = await this.authorizedFetch('/censor/methods', { method: 'GET' });

    if (!response.ok) {
      throw new Error(`Failed to fetch censorship methods: ${response.statusText}`);
    }

    const data = await response.json();
    return data.methods;
  }

  async censorImage(
    file: File, 
    method: string = 'pixelate', 
    parameters: Record<string, any> = {}
  ): Promise<CensorshipResponse> {
    const formData = new FormData();
    formData.append('file', file);

    // Строим URL с query параметрами (FastAPI Query параметры)
    const queryParams = new URLSearchParams();
    Object.entries(parameters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        queryParams.append(key, value.toString());
      }
    });
    
    const path = `/censor/${method}${queryParams.toString() ? '?' + queryParams.toString() : ''}`;

    const response = await this.authorizedFetch(path, {
      method: 'POST',
      body: formData,
    }, { multipart: true });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Censorship failed: ${response.statusText} - ${errorText}`);
    }

    return await response.json();
  }

  async getUserMinioInfo(): Promise<MinioInfo> {
    try {
      console.log('🔑 [API] Getting MinIO info...');
      const response = await this.authorizedFetch('/users/me/minio-info', { method: 'GET' });

      console.log(`📊 [API] MinIO info response: ${response.status} ${response.statusText}`);

      if (!response.ok) {
        const errorText = await response.text();
        console.error(`❌ [API] MinIO info error:`, errorText);
        throw new Error(`Failed to fetch MinIO info: ${response.status} ${response.statusText}`);
      }

      const info = await response.json();
      console.log(`✅ [API] MinIO info:`, info);
      return info;
    } catch (error) {
      console.error('❌ [API] Error fetching MinIO info:', error);
      
      // Возвращаем минимальную информацию с учетом ошибки
      return {
        username: 'unknown',
        files_bucket: 'unknown',
        user_folder: 'unknown',
        storage_used: '0 B',
        provider: 'MinIO',
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  async getSystemStatus(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/debug/system-status`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch system status: ${response.statusText}`);
    }

    return await response.json();
  }

  async getSystemInfo(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/info`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch system info: ${response.statusText}`);
    }

    return await response.json();
  }

  async downloadFile(url: string, filename: string): Promise<void> {
    const response = await fetch(url);
    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  }

  async testFileDownload(objectName: string): Promise<void> {
    // Тестовый метод для проверки скачивания файлов
    const testUrl = `${this.baseUrl}/files/${encodeURIComponent(objectName)}`;
    console.log(`🧪 [API] Testing download from: ${testUrl}`);
    
    try {
      const response = await fetch(testUrl);
      console.log(`📊 [API] Download test response: ${response.status}`);
      
      if (response.ok) {
        console.log(`✅ [API] File download test successful`);
      } else {
        const errorText = await response.text();
        console.error(`❌ [API] Download test failed: ${errorText}`);
      }
    } catch (error) {
      console.error(`💥 [API] Download test exception:`, error);
    }
  }

  clearToken() {
    this.token = null;
    clearAuthCookies();
  }

  async get<T = any>(url: string): Promise<T> {
    const response = await this.authorizedFetch(url, {
      method: 'GET',
    });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || `GET ${url} failed: ${response.status}`);
    }
    return response.json();
  }

  async post<T = any>(url: string, body?: any): Promise<T> {
    const response = await this.authorizedFetch(url, {
      method: 'POST',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || `POST ${url} failed: ${response.status}`);
    }
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return response.json();
    }
    return undefined as T;
  }

  async put<T = any>(url: string, body?: any): Promise<T> {
    const response = await this.authorizedFetch(url, {
      method: 'PUT',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || `PUT ${url} failed: ${response.status}`);
    }
    return response.json();
  }

  async postMultipartJson<T = any>(path: string, formData: FormData): Promise<T> {
    const response = await this.authorizedFetch(
      path,
      { method: 'POST', body: formData },
      { multipart: true }
    );
    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || `POST ${path} failed: ${response.status}`);
    }
    return response.json();
  }

  /** Каталог пользовательских материалов (лаб. №3) */
  async getUserAssetsList(query: Record<string, string | number | boolean | undefined>) {
    const qs = new URLSearchParams();
    Object.entries(query).forEach(([k, v]) => {
      if (v === undefined || v === '') return;
      qs.set(k, String(v));
    });
    const suffix = qs.toString() ? `?${qs.toString()}` : '';
    return this.get(`/user-assets${suffix}`);
  }

  async uploadUserAsset(file: File, meta: { title: string; description?: string; category: string }) {
    const fd = new FormData();
    fd.append('file', file);
    fd.append('title', meta.title);
    if (meta.description) fd.append('description', meta.description);
    fd.append('category', meta.category);
    return this.postMultipartJson('/user-assets', fd);
  }

  async updateUserAsset(
    id: number,
    body: { title?: string; description?: string; category?: string }
  ) {
    return this.put(`/user-assets/${id}`, body);
  }

  async deleteUserAsset(id: number) {
    const response = await this.authorizedFetch(`/user-assets/${id}`, { method: 'DELETE' });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || `DELETE user-asset failed: ${response.status}`);
    }
  }

  async getUserAssetDownloadUrl(id: number, expiresSeconds = 3600) {
    return this.get<{ url: string; expires_in: number }>(
      `/user-assets/${id}/download-url?expires_seconds=${expiresSeconds}`
    );
  }

  async delete<T = any>(url: string): Promise<T> {
    const response = await this.authorizedFetch(url, {
      method: 'DELETE',
    });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || `DELETE ${url} failed: ${response.status}`);
    }
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return response.json();
    }
    return undefined as T;
  }

  /** Публичный endpoint без JWT (прокси в dev на FastAPI). */
  async fetchPublicWeather(city: string): Promise<PublicWeatherPayload> {
    const qs = new URLSearchParams({ city: city.trim() || 'Москва' });
    const path = `/public/weather?${qs.toString()}`;
    const url = path.startsWith('http') ? path : `${this.baseUrl}${path}`;
    const res = await fetch(url);
    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || `Погода: ошибка ${res.status}`);
    }
    return res.json();
  }
}

export const apiService = new ApiService();