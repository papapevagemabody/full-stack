# schemas.py
from pydantic import BaseModel, ConfigDict, EmailStr, validator
from typing import List, Tuple, Any, Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None

class UserCreate(UserBase):
    password: str
    
    @validator('username')
    def username_validator(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        if len(v) > 50:
            raise ValueError('Username must be less than 50 characters')
        return v
    
    @validator('password')
    def password_validator(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v

class User(UserBase):
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    is_active: Optional[bool] = True
    is_admin: Optional[bool] = False
    minio_bucket: Optional[str] = None
    minio_folder: Optional[str] = None
    roles: Optional[List[str]] = []

class UserInDB(User):
    password_hash: str
    minio_access_key: Optional[str] = None
    minio_secret_key: Optional[str] = None
    is_admin: bool = False

class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str

class TokenData(BaseModel):
    username: Optional[str] = None

class Detection(BaseModel):
    type: str
    bbox: Tuple[float, float, float, float]
    confidence: Optional[float] = None  # Добавьте эту строку

class FileResponse(BaseModel):
    id: str
    name: str
    url: str
    detections: List[Detection]
    redactions: List[Any] = []
    object_name: Optional[str] = None
    size: Optional[int] = None
    type: Optional[str] = None
    last_modified: Optional[str] = None

# Модель для регистрации
class UserRegister(BaseModel):
    username: str
    email: Optional[str] = None
    password: str
    
    @validator('password')
    def password_validator(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v

class UserMinioInfo(BaseModel):
    username: str
    minio_access_key: Optional[str]
    minio_bucket: str
    minio_folder: str
    storage_used: str = "0 MB"


# --- Каталог пользовательских материалов (лаб. №3) ---

class UserAssetCreateBody(BaseModel):
    title: str
    description: Optional[str] = None
    category: str = "general"

    @validator("title")
    def title_ok(cls, v):
        v = (v or "").strip()
        if len(v) < 1 or len(v) > 200:
            raise ValueError("title must be 1..200 characters")
        return v

    @validator("category")
    def category_ok(cls, v):
        v = (v or "general").strip() or "general"
        if len(v) > 50:
            raise ValueError("category max 50 characters")
        return v

    @validator("description")
    def desc_ok(cls, v):
        if v is None:
            return None
        v = v.strip()
        if len(v) > 2000:
            raise ValueError("description max 2000 characters")
        return v or None


class UserAssetUpdateBody(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None

    @validator("title")
    def title_ok(cls, v):
        if v is None:
            return None
        v = v.strip()
        if len(v) < 1 or len(v) > 200:
            raise ValueError("title must be 1..200 characters")
        return v

    @validator("category")
    def category_ok(cls, v):
        if v is None:
            return None
        v = v.strip()
        if len(v) > 50:
            raise ValueError("category max 50 characters")
        return v

    @validator("description")
    def desc_ok(cls, v):
        if v is None:
            return None
        v = v.strip()
        if len(v) > 2000:
            raise ValueError("description max 2000 characters")
        return v or None


class UserAssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    owner_username: Optional[str] = None
    title: str
    description: Optional[str] = None
    category: str
    original_filename: str
    content_type: Optional[str] = None
    size_bytes: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserAssetListResponse(BaseModel):
    items: List[UserAssetResponse]
    total: int
    page: int
    page_size: int


class PresignedUrlResponse(BaseModel):
    url: str
    expires_in: int


# --- Лаб. №4: нормализованный ответ внешнего API (погода Open-Meteo) ---
class PublicWeatherResponse(BaseModel):
    available: bool
    city: str
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    temperature_c: Optional[float] = None
    wind_speed_kmh: Optional[float] = None
    weather_code: Optional[int] = None
    provider: str = "open-meteo"
    message: Optional[str] = None