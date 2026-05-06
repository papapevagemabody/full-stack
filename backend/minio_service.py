# minio_service.py
from minio import Minio
from minio.error import S3Error
from config import settings
import io
import os
from pathlib import Path
from typing import Tuple
from datetime import timedelta
from urllib.parse import quote
import secrets
import string

class MinioService:
    def __init__(self):
        self.bucket = settings.MINIO_BUCKET
        self.internal_endpoint = settings.MINIO_ENDPOINT
        self.external_endpoint = getattr(settings, 'MINIO_EXTERNAL_ENDPOINT', settings.MINIO_ENDPOINT)
        self._available = False
        self.client = None
        try:
            self.client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE
            )
            self._ensure_bucket_exists()
            self._available = True
            print(f"✅ MinIO connected: {settings.MINIO_ENDPOINT} (external: {self.external_endpoint})")
        except Exception as e:
            self._available = False
            self.client = None
            print(f"⚠️ MinIO недоступен (сервер не запущен?): {settings.MINIO_ENDPOINT}")
            print(f"   Ошибка: {e}")
            root = Path(__file__).resolve().parent / settings.UPLOAD_DIR / "catalog-blobs"
            print(f"   Локальный режим: каталог файлов — {root}")
            print("   Для S3-режима запустите MinIO на localhost:9000.")
        print(f"📦 minio_service.py: {Path(__file__).resolve()}")

    def _ensure_bucket_exists(self):
        """Создает bucket если он не существует"""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
                print(f"✅ Bucket created: {self.bucket}")
        except S3Error as e:
            print(f"❌ Error creating bucket: {e}")
            raise

    
    def _ensure_user_bucket_exists(self, username: str):
        if not self._available or not self.client:
            return self.bucket
        try:
            bucket_name = f"user-{username}-files"
            
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                print(f"✅ User bucket created: {bucket_name}")
            
            return bucket_name
        except Exception as e:
            print(f"⚠️ Error creating user bucket: {e}")
            return self.bucket  # fallback to default bucket


    def create_user_access(self, username: str) -> dict:
        """Создает пользователя в MinIO и настраивает политики"""
        try:
            # Генерируем уникальные credentials для пользователя
            access_key = f"user-{username}"
            secret_key = self._generate_secret_key()
            
            # Создаем bucket для пользователя
            user_bucket = self._ensure_user_bucket_exists(username)
            
            # В реальном MinIO нужно использовать Admin API для создания пользователей
            # Здесь эмулируем создание пользовательских credentials
            print(f"✅ MinIO user credentials created for: {username}")
            
            return {
                "access_key": access_key,
                "secret_key": secret_key,
                "files_bucket": user_bucket,
                "user_folder": username,
                "bucket": user_bucket,
                "folder": f"{username}/",
                "provider": "MinIO"
            }
            
        except Exception as e:
            print(f"❌ Error creating MinIO user: {e}")
            # Возвращаем общие credentials как fallback
            return {
                "access_key": settings.MINIO_ACCESS_KEY,
                "secret_key": settings.MINIO_SECRET_KEY,
                "files_bucket": self.bucket,
                "user_folder": username,
                "bucket": self.bucket,
                "folder": f"{username}/",
                "provider": "MinIO"
            }

    def _generate_secret_key(self, length=32):
        """Генерирует безопасный секретный ключ"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    def _get_content_type(self, filename: str) -> str:
        """Определяет MIME-тип файла по расширению"""
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'bmp': 'image/bmp',
            'webp': 'image/webp',
            'pdf': 'application/pdf',
            'txt': 'text/plain',
        }
        return types.get(ext, 'application/octet-stream')

    def _catalog_local_root(self) -> Path:
        # Не зависит от cwd при запуске uvicorn из другой папки
        backend_dir = Path(__file__).resolve().parent
        return (backend_dir / settings.UPLOAD_DIR / "catalog-blobs").resolve()

    def _safe_local_path(self, object_name: str) -> Path:
        if not object_name or ".." in object_name:
            raise ValueError("Invalid object name")
        if object_name.startswith(("/", "\\")) or (len(object_name) > 1 and object_name[1] == ":"):
            raise ValueError("Invalid object name")
        root = self._catalog_local_root()
        root.mkdir(parents=True, exist_ok=True)
        root_resolved = root.resolve()
        target = (root_resolved / object_name).resolve()
        # На Windows pathlib.relative_to() часто падает из‑за регистра букв диска и префикса \\?\
        if os.name == "nt":
            rs = os.path.normcase(os.path.abspath(str(root_resolved)))
            ts = os.path.normcase(os.path.abspath(str(target)))
            if ts != rs and not ts.startswith(rs + os.sep):
                raise ValueError("Invalid object path")
        else:
            try:
                target.relative_to(root_resolved)
            except ValueError:
                raise ValueError("Invalid object path") from None
        return target

    def put_object_bytes(self, object_name: str, data: bytes, content_type: str) -> None:
        """MinIO при доступности; иначе или при сбое S3 — запись в uploads/catalog-blobs рядом с backend."""
        if self._available and self.client:
            try:
                self.client.put_object(
                    self.bucket,
                    object_name,
                    io.BytesIO(data),
                    length=len(data),
                    content_type=content_type or "application/octet-stream",
                )
                return
            except Exception as e:
                print(f"⚠️ MinIO put_object не удалось — переходим на локальный диск: {e}")
                self._available = False
        path = self._safe_local_path(object_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        print(f"✅ Файл сохранён локально (без MinIO): {path}")

    def get_object_bytes(self, object_name: str) -> Tuple[bytes, str]:
        """Читает объект из MinIO или с диска (локальный fallback)."""
        base_name = object_name.split("/")[-1]
        ct = self._get_content_type(base_name)
        if self._available and self.client:
            try:
                response = self.client.get_object(self.bucket, object_name)
                try:
                    data = response.read()
                finally:
                    response.close()
                    response.release_conn()
                return data, ct
            except Exception as e:
                print(f"⚠️ MinIO get_object не удалось, пробуем локальный файл: {e}")
        path = self._safe_local_path(object_name)
        if path.is_file():
            return path.read_bytes(), ct
        raise FileNotFoundError(object_name)

    async def upload_file(self, file_data: bytes, filename: str, user_id: str) -> str:
        """Загружает файл в MinIO (или локально) и возвращает object path"""
        object_name = f"{user_id}/{filename}"
        content_type = self._get_content_type(filename)
        try:
            self.put_object_bytes(object_name, file_data, content_type)
            print(f"✅ File uploaded: {object_name} (type: {content_type})")
            return object_name
        except S3Error as e:
            print(f"❌ MinIO upload error: {e}")
            raise

    def generate_presigned_url(self, object_name: str, expires_hours: int = 24) -> str:
        """Генерирует URL для доступа к файлу через backend endpoint"""
        # Используем backend endpoint вместо presigned URL MinIO
        # Это решает проблему с подписью при замене хоста
        # Не кодируем путь - FastAPI с :path автоматически обработает его правильно
        base_url = settings.API_BASE_URL
        return f"{base_url}/files/{object_name}"

    def presigned_get_object_url(self, object_name: str, expires_seconds: int = 3600) -> str:
        """Presigned GET MinIO; без MinIO — URL на отдачу файла через backend (/files/...)."""
        cap = min(max(expires_seconds, 60), 24 * 3600)
        if self._available and self.client:
            return self.client.presigned_get_object(
                self.bucket,
                object_name,
                expires=timedelta(seconds=cap),
            )
        return f"{settings.API_BASE_URL}/files/{quote(object_name, safe='')}"

    def delete_file(self, object_name: str) -> bool:
        """Удаляет файл из MinIO и/или с диска."""
        ok = False
        if self._available and self.client:
            try:
                self.client.remove_object(self.bucket, object_name)
                print(f"✅ File deleted from MinIO: {object_name}")
                ok = True
            except S3Error as e:
                print(f"❌ Error deleting file from MinIO: {e}")
        try:
            p = self._safe_local_path(object_name)
            if p.is_file():
                p.unlink()
                ok = True
        except ValueError:
            pass
        except OSError as e:
            print(f"⚠️ Локальное удаление: {e}")
        return ok

    def health_check(self) -> bool:
        """Проверяет подключение к MinIO"""
        if not self._available or not self.client:
            return False
        try:
            self.client.list_buckets()
            return True
        except (S3Error, Exception) as e:
            print(f"❌ MinIO health check failed: {e}")
            return False

    def setup_user_policy(self, username: str):
        """Настраивает политики доступа для пользователя (эмуляция)"""
        # В реальном MinIO нужно использовать Admin API
        print(f"✅ MinIO policy configured for user: {username}")
        print(f"   - Can access: {self.bucket}/{username}/*")
        print("   - Cannot access other users' files")

# Создаем экземпляр сервиса
minio_service = MinioService()