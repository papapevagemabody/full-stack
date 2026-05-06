# config.py
import os
import socket
from typing import List
from pydantic_settings import BaseSettings

def is_docker_environment():
    """Проверяет, запущен ли код в Docker контейнере"""
    # Проверяем, можем ли мы разрешить имя хоста 'minio' (работает только в Docker сети)
    try:
        socket.gethostbyname('minio')
        return True
    except socket.gaierror:
        return False

class Settings(BaseSettings):
    APP_NAME: str = "Image Redaction API"
    VERSION: str = "2.0.0"
    DEBUG: bool = True
    # test — изолированная SQLite in-memory для pytest (см. backend/tests/conftest.py)
    APP_ENV: str = "development"
    
    # PostgreSQL настройки
    # Значения по умолчанию для локального запуска
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "image_redaction_db"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password123"
    
    # Использовать SQLite вместо PostgreSQL (удобно, если PostgreSQL не установлен)
    USE_SQLITE: bool = True
    
    # MinIO настройки
    # Значения по умолчанию для локального запуска
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_EXTERNAL_ENDPOINT: str = "localhost:9000"  # Для presigned URL (доступен из браузера)
    MINIO_ACCESS_KEY: str = "admin"
    MINIO_SECRET_KEY: str = "password123"
    MINIO_SECURE: bool = False
    MINIO_BUCKET: str = "user-files"
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "env_prefix": ""  # Не используем префикс для переменных окружения
    }
    
    def __init__(self, **kwargs):
        # Переопределяем значения из переменных окружения если они установлены
        super().__init__(**kwargs)
        
        # Если переменные окружения не установлены, используем автоматическое определение
        if "POSTGRES_HOST" not in os.environ:
            self.POSTGRES_HOST = "postgres" if is_docker_environment() else "localhost"
        if "MINIO_ENDPOINT" not in os.environ:
            self.MINIO_ENDPOINT = "minio:9000" if is_docker_environment() else "localhost:9000"
        
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        os.makedirs(self.STATIC_DIR, exist_ok=True)
    
    # CORS настройки
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:8001",
    ]
    
    # Настройки файлов
    UPLOAD_DIR: str = "uploads"
    STATIC_DIR: str = "static"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: set = {".jpg", ".jpeg", ".png", ".gif", ".bmp"}
    
    # Настройки сервера
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    
    # Настройки аутентификации (JWT access + refresh-сессии)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production-2024"

    # --- Лаб. №4: SEO и внешние API ---
    # Публичный URL фронтенда (канонические ссылки и URL в sitemap)
    SITE_PUBLIC_URL: str = "http://localhost:3000"
    # Где объявлен sitemap в robots.txt (часто совпадает с API, например http://127.0.0.1:8001)
    SEO_SITEMAP_ANNOUNCE_URL: str = ""
    # Опциональный ключ для будущих платных гео-API (сейчас не используется — Open-Meteo без ключа)
    EXTERNAL_GEO_API_KEY: str = ""
    EXTERNAL_HTTP_TIMEOUT_SEC: float = 8.0
    EXTERNAL_HTTP_MAX_RETRIES: int = 3
    WEATHER_RATE_LIMIT_PER_MINUTE: int = 40
    
    # Database URL для SQLAlchemy
    @property
    def DATABASE_URL(self) -> str:
        if getattr(self, "APP_ENV", "") == "test":
            return "sqlite:///:memory:"
        if getattr(self, "USE_SQLITE", False):
            return "sqlite:///./image_redaction.db"
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # Base API URL для генерации URL файлов
    @property
    def API_BASE_URL(self):
        return f"http://localhost:{self.PORT}"

    @property
    def sitemap_announce_url(self) -> str:
        if self.SEO_SITEMAP_ANNOUNCE_URL and self.SEO_SITEMAP_ANNOUNCE_URL.strip():
            return self.SEO_SITEMAP_ANNOUNCE_URL.strip().rstrip("/")
        return self.API_BASE_URL.rstrip("/")

settings = Settings()