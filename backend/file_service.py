# file_service.py
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List
from fastapi import UploadFile, HTTPException
from config import settings
from file_utils import file_utils
from face_detection import face_detector
from schemas import FileResponse

class FileService:
    def __init__(self):
        self.face_detector = face_detector
    
    async def upload_file(self, file: UploadFile, current_user) -> FileResponse:
        try:
            filename = await file_utils.save_upload_file(file, settings.UPLOAD_DIR)
            
            upload_path = os.path.join(settings.UPLOAD_DIR, filename)
            static_path = os.path.join(settings.STATIC_DIR, filename)
            
            with open(upload_path, "rb") as source, open(static_path, "wb") as target:
                target.write(source.read())
            
            detections = self.face_detector.detect_faces(upload_path)

            # Пишем объект так, чтобы его можно было увидеть в /files (MinIO или локальный fallback)
            from minio_service import minio_service
            content_type = file.content_type or self._get_file_type(filename)
            object_name = f"{current_user.username}/{filename}"

            with open(upload_path, "rb") as f:
                file_data = f.read()

            # minio_service.put_object_bytes в режиме без MinIO сохраняет на диск
            minio_service.put_object_bytes(object_name, file_data, content_type)

            file_url = minio_service.generate_presigned_url(object_name)

            stat = os.stat(upload_path)
            return FileResponse(
                id=filename.split('.')[0],
                name=file.filename,
                url=file_url,
                object_name=object_name,
                size=stat.st_size,
                type=content_type,
                last_modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                detections=detections,
                redactions=[],
            )
            
        except Exception as e:
            if 'filename' in locals():
                file_utils.delete_file(filename, settings.UPLOAD_DIR)
                file_utils.delete_file(filename, settings.STATIC_DIR)
            raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")
    
    async def upload_multiple_files(self, files: List[UploadFile], current_user) -> List[FileResponse]:
        responses = []
        for file in files:
            response = await self.upload_file(file, current_user)
            responses.append(response)
        return responses
    
    def get_all_files(self) -> List[FileResponse]:
        return []
    
    def delete_file(self, object_name: str) -> bool:
        """
        Удаляет файл из MinIO по object_name
        """
        try:
            from minio_service import minio_service
            
            print(f"🗑️ [FileService] Deleting file from MinIO: {object_name}")
            
            # Удаляем файл из MinIO
            success = minio_service.delete_file(object_name)
            
            if success:
                print(f"✅ [FileService] File deleted successfully: {object_name}")
            else:
                print(f"⚠️ [FileService] File deletion returned False: {object_name}")
            
            return success
        except Exception as e:
            print(f"❌ [FileService] Error deleting file: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Ошибка при удалении файла: {str(e)}")

    async def get_user_files(self, username: str) -> List[FileResponse]:
        """
        Получение списка файлов пользователя из MinIO
        """
        try:
            from minio_service import minio_service
            # Локальный режим: читаем то, что было сохранено minio_service.put_object_bytes
            if not getattr(minio_service, 'client', None) or not getattr(minio_service, '_available', False):
                root = Path(__file__).resolve().parent / settings.UPLOAD_DIR / "catalog-blobs"
                if not root.exists():
                    return []

                files: List[FileResponse] = []
                prefix = f"{username}/"
                for p in root.rglob("*"):
                    if not p.is_file():
                        continue
                    rel = p.relative_to(root).as_posix()
                    if not rel.startswith(prefix):
                        continue

                    stat = p.stat()
                    fname = p.name
                    content_type = self._get_file_type(fname)
                    files.append(
                        FileResponse(
                            id=str(uuid.uuid4()),
                            name=fname,
                            url=minio_service.generate_presigned_url(rel),
                            object_name=rel,
                            size=stat.st_size,
                            type=content_type,
                            last_modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            detections=[],
                            redactions=[],
                        )
                    )
                return files
            
            print(f"🔍 [FileService] Getting files for user: {username}")
            print(f"📦 Bucket: {minio_service.bucket}")
            
            files = []
            
            try:
                # Получаем список объектов из MinIO
                print(f"🔍 Listing objects with prefix: {username}/")
                
                # Получаем все объекты
                objects = minio_service.client.list_objects(
                    minio_service.bucket,
                    prefix=f"{username}/",
                    recursive=True
                )
                
                # Конвертируем в список
                object_list = list(objects)
                print(f"✅ Found {len(object_list)} objects in MinIO")
                
                # Обрабатываем каждый объект
                for obj in object_list:
                    try:
                        print(f"📄 Processing object: {obj.object_name}")
                        
                        # Получаем полную информацию об объекте
                        try:
                            stat = minio_service.client.stat_object(
                                minio_service.bucket,
                                obj.object_name
                            )
                            size = stat.size
                            content_type = stat.content_type
                            last_modified = stat.last_modified
                            print(f"📊 Stat: size={size}, type={content_type}")
                        except Exception as stat_error:
                            print(f"⚠️ Cannot stat object, using defaults: {stat_error}")
                            size = obj.size if hasattr(obj, 'size') else 0
                            content_type = self._get_file_type(obj.object_name)
                            last_modified = datetime.now()
                        
                        # Генерируем временную ссылку
                        try:
                            url = minio_service.generate_presigned_url(obj.object_name)
                            print(f"🔗 Generated URL: {url[:100]}...")
                        except Exception as url_error:
                            print(f"⚠️ Cannot generate presigned URL: {url_error}")
                            url = f"http://localhost:9000/{minio_service.bucket}/{obj.object_name}"
                        
                        # Извлекаем имя файла
                        filename = obj.object_name.split("/")[-1] if "/" in obj.object_name else obj.object_name
                        
                        # Создаем FileResponse
                        file_response = FileResponse(
                            id=str(uuid.uuid4()),
                            name=filename,
                            url=url,
                            object_name=obj.object_name,
                            size=size,
                            type=content_type or self._get_file_type(obj.object_name),
                            last_modified=last_modified.isoformat() if hasattr(last_modified, 'isoformat') else str(last_modified),
                            detections=[],
                            redactions=[]
                        )
                        
                        files.append(file_response)
                        print(f"✅ Added file: {filename} ({size} bytes)")
                        
                    except Exception as e:
                        print(f"❌ Error processing object {obj.object_name}: {e}")
                        import traceback
                        traceback.print_exc()
                        continue
                
            except Exception as e:
                print(f"❌ Error listing objects: {e}")
                import traceback
                traceback.print_exc()
            
            print(f"📊 Total files to return: {len(files)}")
            
            return files
            
        except Exception as e:
            print(f"❌ [FileService] Error getting user files: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _get_file_type(self, filename: str) -> str:
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

file_service = FileService()