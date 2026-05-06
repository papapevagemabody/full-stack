# app.py
from fastapi import FastAPI, Request, UploadFile, File, Depends, HTTPException, status, Query
from fastapi.exceptions import ResponseValidationError
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm
from typing import List, Optional
import os
import uuid
import random
from contextlib import asynccontextmanager
from censorship_service import censorship_service

# Импорты из schemas
from schemas import (
    FileResponse,
    User,
    Token,
    UserRegister,
    RefreshTokenRequest,
    LogoutRequest,
)

# Импорты из auth
from auth import (
    authenticate_user,
    get_current_active_user,
    create_user,
    require_permission,
    require_admin,
    initialize_demo_users,
)
from token_session_service import (
    TokenSessionService,
    get_token_session_service,
    InvalidRefreshTokenError,
    RefreshTokenReuseError,
)

# Импорты из сервисов
from file_service import file_service
from minio_service import minio_service
from user_service import user_service
from rbac_service import rbac_service

# Импорты для базы данных
from database import create_tables, check_connection

from user_assets_routes import router as user_assets_router
from user_asset_service import user_asset_service
from seo_routes import router as seo_router
from public_api_routes import router as public_api_router


def _catalog_register_file_response(current_user: User, r: FileResponse) -> None:
    """Добавляет запись в каталог user_assets после загрузки в MinIO (если есть catalog.view)."""
    if not r.object_name:
        return
    user_asset_service.try_register_after_storage(
        current_user,
        object_name=r.object_name,
        original_filename=r.name or "",
        size_bytes=r.size or 0,
        content_type=r.type,
        category="upload",
        title=r.name,
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    # При запуске приложения
    print("=" * 50)
    print("🚀 Запуск приложения...")
    print("=" * 50)
    
    # Проверяем подключение к PostgreSQL
    print("🔄 Проверка подключения к PostgreSQL...")
    if check_connection():
        print("✅ PostgreSQL подключен")
    else:
        print("❌ Не удалось подключиться к PostgreSQL")
    
    # Создаем таблицы если их нет
    print("🔄 Создание таблиц в PostgreSQL...")
    try:
        create_tables()
        print("✅ Таблицы созданы")
    except Exception as e:
        print(f"❌ Ошибка при создании таблиц: {e}")
    
    # Создаем демо пользователей
    print("🔄 Инициализация демо пользователей...")
    try:
        initialize_demo_users()
        print("✅ Демо пользователи созданы")
    except Exception as e:
        print(f"⚠️ Ошибка при создании демо пользователей: {e}")
    
    print("=" * 50)
    print("✅ Приложение запущено и готово к работе!")
    print("=" * 50)
    
    yield  # Приложение работает
    
    # При остановке приложения
    print("🔄 Остановка приложения...")

# Создаем необходимые папки
os.makedirs("uploads", exist_ok=True)
os.makedirs("static", exist_ok=True)

app = FastAPI(
    title="Image Redaction API",
    description="API для обнаружения и цензурирования лиц на изображениях с хранением в MinIO",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan  # Добавляем lifespan
)


@app.exception_handler(ResponseValidationError)
async def response_validation_exception_handler(request: Request, exc: ResponseValidationError):
    """Прозрачная диагностика вместо голого HTTP 500 при несовпадении ответа с response_model."""
    print(f"❌ ResponseValidationError {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Ответ API не прошёл проверку схемы", "validation_errors": exc.errors()},
    )


# CORS настройки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(user_assets_router)
app.include_router(seo_router)
app.include_router(public_api_router)

# Все остальные маршруты остаются без изменений...
# [ОСТАЛЬНОЙ КОД ОСТАЕТСЯ БЕЗ ИЗМЕНЕНИЙ]

# Public routes
@app.get("/")
async def root():
    return {
        "message": "Image Redaction API with PostgreSQL & MinIO Storage", 
        "version": "2.0.0",
        "docs": "/api/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Проверка здоровья API и подключений"""
    minio_health = minio_service.health_check()
    user_service_health = user_service.health_check()
    postgres_connected = check_connection()
    
    return {
        "status": "healthy", 
        "app": "Image Redaction API", 
        "version": "2.0.0",
        "postgres_connected": postgres_connected,
        "minio_connected": minio_health,
        "user_service_connected": user_service_health,
        "storage": "MinIO",
        "database": "PostgreSQL"
    }

# Authentication routes
@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session_service: TokenSessionService = Depends(get_token_session_service),
):
    """
    Вход: выдача короткоживущего access JWT и долгоживущего refresh (ротация на /auth/refresh).
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token, refresh_token, expires_in = session_service.issue_tokens_for_user(user)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
        "expires_in": expires_in,
    }


@app.post("/auth/refresh", response_model=Token)
async def auth_refresh_tokens(
    body: RefreshTokenRequest,
    session_service: TokenSessionService = Depends(get_token_session_service),
):
    """Обновление access по refresh с ротацией refresh в БД."""
    try:
        access_token, refresh_token, expires_in = session_service.rotate_refresh(body.refresh_token)
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "refresh_token": refresh_token,
            "expires_in": expires_in,
        }
    except RefreshTokenReuseError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token reuse detected; all sessions in this family revoked",
        )
    except InvalidRefreshTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )


@app.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def auth_logout(
    body: LogoutRequest,
    session_service: TokenSessionService = Depends(get_token_session_service),
):
    """Отзыв текущей refresh-сессии на сервере (клиент удаляет токены локально)."""
    session_service.revoke_refresh(body.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.post("/register", response_model=User)
async def register_user(user_data: UserRegister):
    """
    Регистрация нового пользователя с привязкой к MinIO
    """
    try:
        user = create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password
        )
        
        print(f"✅ User registration completed: {user_data.username}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Получение информации о текущем пользователе
    """
    return current_user

@app.get("/users/me/minio-info")
async def get_user_minio_info(current_user: User = Depends(get_current_active_user)):
    """
    Получение MinIO информации для текущего пользователя
    """
    user_data = user_service.get_user(current_user.username)
    if not user_data:
        raise HTTPException(404, "User data not found")
    
    return {
        "username": current_user.username,
        "minio_access_key": user_data.get("minio_access_key"),
        "files_bucket": user_data.get("files_bucket"),
        "user_folder": user_data.get("user_folder"),
        "storage_used": "0 MB"
    }

# File management routes
@app.post("/upload", response_model=FileResponse)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(require_permission("files.upload"))
):
    """
    Загрузка одного файла с автоматическим обнаружением лиц
    Требуется разрешение: files.upload
    """
    try:
        out = await file_service.upload_file(file, current_user)
        _catalog_register_file_response(current_user, out)
        return out
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при загрузке файла: {str(e)}"
        )

@app.post("/upload-multiple", response_model=List[FileResponse])
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(require_permission("files.upload"))
):
    """
    Загрузка нескольких файлов с автоматическим обнаружением лиц
    Требуется разрешение: files.upload
    """
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не переданы файлы"
        )
    
    try:
        out = await file_service.upload_multiple_files(files, current_user)
        for item in out:
            _catalog_register_file_response(current_user, item)
        return out
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при загрузке файлов: {str(e)}"
        )

@app.get("/files", response_model=List[FileResponse])
async def get_files(current_user: User = Depends(require_permission("files.view_own"))):
    """
    Получение списка загруженных файлов пользователя из MinIO
    Требуется разрешение: files.view_own
    """
    try:
        return await file_service.get_user_files(current_user.username)
    except Exception as e:
        print(f"❌ Error getting files: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении списка файлов: {str(e)}"
        )

@app.get("/files/{object_name:path}")
async def get_file(object_name: str):
    """
    Получение файла из MinIO через backend (прокси)
    Доступ открыт для файлов с правильным путем (username в пути)
    """
    try:
        # Декодируем путь на случай двойного кодирования
        from urllib.parse import unquote
        object_name = unquote(object_name)
        
        # Проверяем что путь содержит username (базовая проверка безопасности)
        if not "/" in object_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file path"
            )
        
        print(f"📥 Requested file: {object_name}")

        from minio_service import minio_service
        from fastapi.responses import Response

        try:
            file_data, content_type = minio_service.get_object_bytes(object_name)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file path",
            )
        except FileNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found",
            )

        return Response(
            content=file_data,
            media_type=content_type,
            headers={
                "Content-Disposition": f'inline; filename="{object_name.split("/")[-1]}"'
            },
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении файла: {str(e)}"
        )

@app.delete("/files/{object_name:path}")
async def delete_file(
    object_name: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Удаление файла по его object_name в MinIO
    Требуется разрешение: files.delete_own (для своих файлов) или files.delete_all (для всех)
    """
    try:
        # Декодируем путь на случай кодирования
        from urllib.parse import unquote
        object_name = unquote(object_name)
        
        # Проверяем права доступа
        is_own_file = object_name.startswith(f"{current_user.username}/")
        can_delete_all = rbac_service.user_has_permission(current_user.username, "files.delete_all")
        
        if not is_own_file and not can_delete_all:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied - you can only delete your own files"
            )
        
        if is_own_file and not rbac_service.user_has_permission(current_user.username, "files.delete_own"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: files.delete_own"
            )
        
        print(f"🗑️ [API] Deleting file: {object_name} for user: {current_user.username}")
        
        success = file_service.delete_file(object_name)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        return {
            "success": True, 
            "message": "Файл удален",
            "object_name": object_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при удалении файла: {str(e)}"
        )

# Debug routes
@app.get("/debug/system-status")
async def debug_system_status():
    """
    Полная информация о состоянии системы
    """
    from database import check_connection
    
    try:
        users = user_service.get_all_users()
    except:
        users = []
    
    return {
        "api_version": "2.0.0",
        "storage_backend": "MinIO",
        "database": "PostgreSQL",
        "postgres_connected": check_connection(),
        "minio_connected": minio_service.health_check(),
        "total_users": len(users),
        "tables_created": True,
        "services": {
            "postgres": check_connection(),
            "minio": minio_service.health_check(),
            "user_service": user_service.health_check()
        }
    }

@app.get("/info")
async def get_system_info():
    """
    Получение информации о системе и настройках
    """
    return {
        "app_name": "Image Redaction API",
        "version": "2.0.0",
        "database": "PostgreSQL",
        "file_storage": "MinIO",
        "authentication": "JWT access + refresh sessions (PostgreSQL)",
        "features": {
            "face_detection": True,
            "user_management": True,
            "file_upload": True,
            "user_registration": True
        }
    }


@app.post("/censor/pixelate")
async def pixelate_faces(
    file: UploadFile = File(...),
    pixel_size: int = Query(15, ge=5, le=50),
    current_user: User = Depends(require_permission("censor.use"))
):
    """
    Пикселизация лиц на изображении
    Требуется разрешение: censor.use
    """
    try:
        # Сохраняем временный файл
        import tempfile
        import shutil
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            temp_path = tmp_file.name
        
        # Применяем пикселизацию
        result_path = censorship_service.pixelate_face(temp_path, pixel_size)
        
        if not result_path or not os.path.exists(result_path):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка при обработке изображения"
            )
        
        # Загружаем обработанный файл в MinIO
        processed_filename = os.path.basename(result_path)
        with open(result_path, "rb") as f:
            file_data = f.read()
        
        # Сохраняем в MinIO
        object_name = await minio_service.upload_file(
            file_data, 
            processed_filename, 
            current_user.username
        )
        
        # Генерируем URL
        file_url = minio_service.generate_presigned_url(object_name)

        user_asset_service.try_register_after_storage(
            current_user,
            object_name=object_name,
            original_filename=processed_filename or (file.filename or "censored.jpg"),
            size_bytes=len(file_data),
            content_type="image/jpeg",
            category="censored",
            title=f"Цензура: {file.filename or 'изображение'}",
        )
        
        # Очищаем временные файлы
        os.unlink(temp_path)
        if result_path != temp_path:
            os.unlink(result_path)
        
        return {
            "success": True,
            "message": "Изображение успешно обработано",
            "original_filename": file.filename,
            "processed_filename": processed_filename,
            "object_name": object_name,
            "url": file_url,
            "censorship_method": "pixelation",
            "pixel_size": pixel_size
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при цензурировании: {str(e)}"
        )

@app.get("/censor/methods")
async def get_censorship_methods():
    """
    Получение доступных методов цензурирования
    """
    return {
        "methods": [
            {
                "id": "pixelate",
                "name": "Пикселизация",
                "description": "Преобразует области лиц в пиксели",
                "parameters": [
                    {
                        "name": "pixel_size",
                        "type": "integer",
                        "min": 5,
                        "max": 50,
                        "default": 15,
                        "description": "Размер пикселя (меньше = более грубая пикселизация)"
                    }
                ]
            },
            {
                "id": "blur",
                "name": "Размытие",
                "description": "Применяет Gaussian blur к лицам",
                "parameters": [
                    {
                        "name": "blur_strength",
                        "type": "integer",
                        "min": 5,
                        "max": 101,
                        "default": 31,
                        "description": "Сила размытия (только нечетные числа)"
                    }
                ]
            },
            {
                "id": "black_bar",
                "name": "Черные полосы",
                "description": "Накладывает черные прямоугольники на лица",
                "parameters": []
            }
        ]
    }

# RBAC Management endpoints (только для администраторов)
@app.get("/admin/roles")
async def get_all_roles(current_user: User = Depends(require_admin)):
    """
    Получение всех ролей в системе
    Требуется роль: admin
    """
    try:
        roles = rbac_service.get_all_roles()
        return {"roles": roles}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении ролей: {str(e)}"
        )

@app.get("/admin/permissions")
async def get_all_permissions(current_user: User = Depends(require_admin)):
    """
    Получение всех разрешений в системе
    Требуется роль: admin
    """
    try:
        permissions = rbac_service.get_all_permissions()
        return {"permissions": permissions}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении разрешений: {str(e)}"
        )

@app.get("/admin/users/{username}/roles")
async def get_user_roles(username: str, current_user: User = Depends(require_admin)):
    """
    Получение ролей пользователя
    Требуется роль: admin
    """
    try:
        roles = rbac_service.get_user_roles(username)
        permissions = rbac_service.get_user_permissions(username)
        return {
            "username": username,
            "roles": roles,
            "permissions": permissions
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении ролей пользователя: {str(e)}"
        )

@app.post("/admin/users/{username}/roles/{role_name}")
async def assign_role_to_user(
    username: str,
    role_name: str,
    current_user: User = Depends(require_admin)
):
    """
    Назначение роли пользователю
    Требуется роль: admin
    """
    try:
        success = rbac_service.assign_role_to_user(username, role_name)
        if success:
            return {
                "success": True,
                "message": f"Роль {role_name} успешно назначена пользователю {username}",
                "username": username,
                "role": role_name
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Не удалось назначить роль {role_name} пользователю {username}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при назначении роли: {str(e)}"
        )

@app.delete("/admin/users/{username}/roles/{role_name}")
async def remove_role_from_user(
    username: str,
    role_name: str,
    current_user: User = Depends(require_admin)
):
    """
    Удаление роли у пользователя
    Требуется роль: admin
    """
    try:
        success = rbac_service.remove_role_from_user(username, role_name)
        if success:
            return {
                "success": True,
                "message": f"Роль {role_name} успешно удалена у пользователя {username}",
                "username": username,
                "role": role_name
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Не удалось удалить роль {role_name} у пользователя {username}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при удалении роли: {str(e)}"
        )

@app.get("/admin/users")
async def get_all_users(current_user: User = Depends(require_permission("users.view"))):
    """
    Получение списка всех пользователей
    Требуется разрешение: users.view
    """
    try:
        users = user_service.get_all_users()
        # Добавляем информацию о ролях для каждого пользователя
        users_with_roles = []
        for user in users:
            roles = rbac_service.get_user_roles(user["username"])
            user["roles"] = roles
            users_with_roles.append(user)
        return {"users": users_with_roles}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении списка пользователей: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8001,
        reload=False
    )