# user_asset_service.py — бизнес-логика каталога + MinIO
from __future__ import annotations

import re
import traceback
import uuid
from datetime import date
from typing import Optional

from fastapi import HTTPException, UploadFile
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError

from config import settings
from database import get_db_context
from minio_service import minio_service
from rbac_service import rbac_service
from repositories.user_asset_repository import UserAssetRepository, user_asset_repository, SortField, SortOrder
from schemas import User as UserSchema
from schemas import UserAssetListResponse, UserAssetResponse, UserAssetUpdateBody


class UserAssetService:
    def __init__(self, repo: UserAssetRepository):
        self._repo = repo

    def _to_response(self, row) -> UserAssetResponse:
        owner = getattr(row, "owner", None)
        return UserAssetResponse(
            id=row.id,
            user_id=row.user_id,
            owner_username=owner.username if owner else None,
            title=row.title,
            description=row.description,
            category=row.category,
            original_filename=row.original_filename,
            content_type=row.content_type,
            size_bytes=row.size_bytes,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def _can_access(self, current_user: UserSchema, row, *, write: bool) -> None:
        if row.user_id == current_user.id:
            return
        if write:
            raise HTTPException(status_code=403, detail="Нельзя изменять чужие записи")
        if rbac_service.user_has_permission(current_user.username, "files.view_all"):
            return
        raise HTTPException(status_code=403, detail="Доступ запрещён")

    def _can_modify(self, current_user: UserSchema, row) -> None:
        if row.user_id == current_user.id:
            return
        if rbac_service.user_has_permission(current_user.username, "files.delete_all") and rbac_service.user_has_permission(
            current_user.username, "files.view_all"
        ):
            return
        raise HTTPException(status_code=403, detail="Нельзя изменять чужую запись")

    def list_assets(
        self,
        current_user: UserSchema,
        *,
        q: Optional[str],
        category: Optional[str],
        date_from: Optional[date],
        date_to: Optional[date],
        page: int,
        page_size: int,
        sort_by: SortField,
        sort_order: SortOrder,
        all_users: bool,
    ) -> UserAssetListResponse:
        if not rbac_service.user_has_permission(current_user.username, "catalog.view"):
            raise HTTPException(status_code=403, detail="Нет права catalog.view")

        owner_id: Optional[int]
        if all_users:
            if not rbac_service.user_has_permission(current_user.username, "files.view_all"):
                raise HTTPException(status_code=403, detail="Только администратор может смотреть все записи")
            owner_id = None
        else:
            if current_user.id is None:
                raise HTTPException(status_code=400, detail="Некорректный пользователь")
            owner_id = current_user.id

        try:
            with get_db_context() as db:
                rows, total = self._repo.list_filtered(
                    db,
                    owner_user_id=owner_id,
                    q=q,
                    category=category,
                    date_from=date_from,
                    date_to=date_to,
                    sort_by=sort_by,
                    sort_order=sort_order,
                    page=page,
                    page_size=page_size,
                )
                items = [self._to_response(r) for r in rows]
                db.commit()
        except OperationalError as e:
            err = str(e).lower()
            if "no such table" in err or "user_assets" in err:
                raise HTTPException(
                    status_code=503,
                    detail="Таблица каталога (user_assets) не найдена. Перезапустите backend, чтобы выполнился create_tables.",
                ) from e
            raise HTTPException(status_code=503, detail=f"Ошибка базы данных: {e}") from e
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Ошибка базы данных: {e}") from e

        return UserAssetListResponse(items=items, total=total, page=page, page_size=page_size)

    def get_one(self, current_user: UserSchema, asset_id: int) -> UserAssetResponse:
        if not rbac_service.user_has_permission(current_user.username, "catalog.view"):
            raise HTTPException(status_code=403, detail="Нет права catalog.view")
        with get_db_context() as db:
            row = self._repo.get_by_id(db, asset_id)
            if not row:
                raise HTTPException(status_code=404, detail="Запись не найдена")
            self._can_access(current_user, row, write=False)
            out = self._to_response(row)
            db.commit()
        return out

    async def create_with_upload(
        self,
        current_user: UserSchema,
        file: UploadFile,
        title: str,
        description: Optional[str],
        category: str,
    ) -> UserAssetResponse:
        if not rbac_service.user_has_permission(current_user.username, "catalog.manage"):
            raise HTTPException(status_code=403, detail="Нет права catalog.manage")
        if not rbac_service.user_has_permission(current_user.username, "files.upload"):
            raise HTTPException(status_code=403, detail="Нет права files.upload")
        if current_user.id is None:
            raise HTTPException(status_code=400, detail="Некорректный пользователь")

        raw = await file.read()
        size = len(raw)
        if size == 0:
            raise HTTPException(status_code=400, detail="Пустой файл")
        if size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Файл слишком большой (макс. {settings.MAX_FILE_SIZE} байт)",
            )

        orig = (file.filename or "unnamed").split("/")[-1].split("\\")[-1]
        ext = ""
        if "." in orig:
            ext = "." + orig.lower().rsplit(".", 1)[-1]
        if ext and ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Тип файла не разрешён. Допустимо: {', '.join(sorted(settings.ALLOWED_EXTENSIONS))}",
            )

        safe = re.sub(r"[^a-zA-Z0-9._-]", "_", orig)[:120] or "file"
        object_name = f"{current_user.username}/assets/{uuid.uuid4().hex}_{safe}"
        content_type = file.content_type or minio_service._get_content_type(safe)

        try:
            minio_service.put_object_bytes(object_name, raw, content_type)
        except Exception as e:
            print(f"❌ Ошибка хранилища (каталог): {type(e).__name__}: {e}")
            traceback.print_exc()
            raise HTTPException(status_code=503, detail=f"Ошибка загрузки в хранилище: {e}")

        new_id: int
        try:
            with get_db_context() as db:
                row = self._repo.create(
                    db,
                    user_id=current_user.id,
                    title=title.strip(),
                    description=description,
                    category=category,
                    object_name=object_name,
                    original_filename=orig,
                    content_type=content_type,
                    size_bytes=size,
                )
                db.flush()
                new_id = row.id
                db.commit()
        except IntegrityError as e:
            raise HTTPException(status_code=409, detail=f"Конфликт при сохранении записи: {e}") from e
        except OperationalError as e:
            raise HTTPException(status_code=503, detail=f"Ошибка базы данных: {e}") from e
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Ошибка базы данных: {e}") from e

        with get_db_context() as db:
            row = self._repo.get_by_id(db, new_id)
            if not row:
                raise HTTPException(status_code=500, detail="Не удалось прочитать созданную запись")
            out = self._to_response(row)
            db.commit()
        return out

    def try_register_after_storage(
        self,
        current_user: UserSchema,
        *,
        object_name: Optional[str],
        original_filename: str,
        size_bytes: int,
        content_type: Optional[str],
        category: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        """
        Создаёт запись каталога для уже загруженного в хранилище объекта (лаб. №3 + профиль).
        Вызывается после /upload, /upload-multiple, /censor/* — без отдельного запроса с фронта.
        Требуется право catalog.view; при отсутствии — тихий выход.
        """
        if not object_name or not object_name.strip():
            return
        if not rbac_service.user_has_permission(current_user.username, "catalog.view"):
            return
        if current_user.id is None:
            return
        prefix = f"{current_user.username}/"
        if not object_name.startswith(prefix):
            return

        orig = (original_filename or "file").split("/")[-1].split("\\")[-1][:255]
        title_use = (title or orig or "файл").strip()[:200]
        cat = (category or "general").strip()[:50] or "general"
        size = max(0, int(size_bytes) if size_bytes is not None else 0)

        try:
            with get_db_context() as db:
                if self._repo.get_by_object_name(db, object_name):
                    db.commit()
                    return
                self._repo.create(
                    db,
                    user_id=current_user.id,
                    title=title_use,
                    description=description,
                    category=cat,
                    object_name=object_name,
                    original_filename=orig,
                    content_type=content_type,
                    size_bytes=size,
                )
                db.commit()
        except IntegrityError:
            return
        except Exception as e:
            print(f"⚠️ try_register_after_storage: {type(e).__name__}: {e}")
            traceback.print_exc()

    def update_meta(self, current_user: UserSchema, asset_id: int, body: UserAssetUpdateBody) -> UserAssetResponse:
        if not rbac_service.user_has_permission(current_user.username, "catalog.manage"):
            raise HTTPException(status_code=403, detail="Нет права catalog.manage")

        data = body.model_dump(exclude_unset=True) if hasattr(body, "model_dump") else body.dict(exclude_unset=True)
        if not data:
            raise HTTPException(status_code=400, detail="Нет полей для обновления")

        with get_db_context() as db:
            row = self._repo.get_by_id(db, asset_id)
            if not row:
                raise HTTPException(status_code=404, detail="Запись не найдена")
            self._can_modify(current_user, row)
            if "title" in data and data["title"] is not None:
                row.title = data["title"]
            if "description" in data:
                row.description = data["description"]
            if "category" in data and data["category"] is not None:
                row.category = data["category"]
            self._repo.save(db, row)
            db.commit()
            row = self._repo.get_by_id(db, asset_id)
            out = self._to_response(row)
            db.commit()
        return out

    def delete_asset(self, current_user: UserSchema, asset_id: int) -> None:
        if not rbac_service.user_has_permission(current_user.username, "catalog.manage"):
            raise HTTPException(status_code=403, detail="Нет права catalog.manage")
        if not rbac_service.user_has_permission(current_user.username, "files.delete_own"):
            raise HTTPException(status_code=403, detail="Нет права files.delete_own")

        with get_db_context() as db:
            row = self._repo.get_by_id(db, asset_id)
            if not row:
                raise HTTPException(status_code=404, detail="Запись не найдена")
            self._can_modify(current_user, row)
            oname = row.object_name
            self._repo.delete(db, row)
            db.commit()

        ok = minio_service.delete_file(oname)
        if not ok:
            # метаданные уже удалены; файл мог отсутствовать в MinIO
            pass

    def presigned_download(self, current_user: UserSchema, asset_id: int, expires_seconds: int = 3600) -> tuple[str, int]:
        if not rbac_service.user_has_permission(current_user.username, "catalog.view"):
            raise HTTPException(status_code=403, detail="Нет права catalog.view")
        with get_db_context() as db:
            row = self._repo.get_by_id(db, asset_id)
            if not row:
                raise HTTPException(status_code=404, detail="Запись не найдена")
            self._can_access(current_user, row, write=False)
            oname = row.object_name
            db.commit()
        try:
            cap = min(max(expires_seconds, 60), 24 * 3600)
            url = minio_service.presigned_get_object_url(oname, expires_seconds=cap)
            return url, cap
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Не удалось выдать ссылку: {e}")


def get_user_asset_service() -> UserAssetService:
    return user_asset_service


user_asset_service = UserAssetService(user_asset_repository)
