# token_session_service.py — сервисный слой: выпуск, ротация и отзыв refresh-сессий
from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Tuple

from config import settings
from database import get_db_context
from models import User as UserModel
from rbac_service import rbac_service
from repositories.refresh_session_repository import RefreshSessionRepository, refresh_session_repository
from schemas import User as UserSchema


def _hash_refresh_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class TokenSessionError(Exception):
    """Базовая ошибка операций с refresh-сессией."""


class InvalidRefreshTokenError(TokenSessionError):
    pass


class RefreshTokenReuseError(TokenSessionError):
    """Повторное использование отозванного refresh — отзыв всего семейства."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class TokenSessionService:
    def __init__(self, repo: RefreshSessionRepository):
        self._repo = repo

    def _user_schema_from_db_user(self, row: UserModel) -> UserSchema:
        roles = rbac_service.get_user_roles(row.username)
        return UserSchema(
            id=row.id,
            username=row.username,
            email=row.email,
            created_at=row.created_at,
            is_active=row.is_active,
            is_admin=row.is_admin,
            minio_bucket=row.minio_bucket,
            minio_folder=row.minio_folder,
            roles=roles,
        )

    def issue_tokens_for_user(self, user: UserSchema) -> Tuple[str, str, int]:
        """Возвращает (access_jwt, refresh_plain, expires_in_seconds)."""
        if user.id is None:
            raise ValueError("User id required for session issue")

        from auth import create_access_token

        access_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access = create_access_token(
            data={"sub": user.username},
            expires_delta=access_delta,
        )
        refresh_plain = secrets.token_urlsafe(48)
        family_id = str(uuid.uuid4())
        expires_at = _utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        token_hash = _hash_refresh_token(refresh_plain)

        with get_db_context() as db:
            self._repo.add(
                db,
                user_id=user.id,
                token_hash=token_hash,
                family_id=family_id,
                expires_at=expires_at,
            )
            db.commit()

        expires_in = int(access_delta.total_seconds())
        return access, refresh_plain, expires_in

    def rotate_refresh(self, refresh_plain: str) -> Tuple[str, str, int]:
        """
        Ротация: один действующий refresh → новая пара access+refresh.
        При reuse отозванного токена — отзыв семейства (компрометация).
        """
        if not refresh_plain or not refresh_plain.strip():
            raise InvalidRefreshTokenError("Missing refresh token")

        from auth import create_access_token

        th = _hash_refresh_token(refresh_plain)

        with get_db_context() as db:
            row = self._repo.get_by_token_hash(db, th)
            if row is None:
                raise InvalidRefreshTokenError("Invalid refresh token")

            if row.revoked:
                self._repo.revoke_family(db, row.family_id)
                db.commit()
                raise RefreshTokenReuseError("Refresh token reuse detected")

            if _as_utc(row.expires_at) < _utcnow():
                self._repo.mark_revoked(db, row.id)
                db.commit()
                raise InvalidRefreshTokenError("Refresh token expired")

            user_row = db.query(UserModel).filter(UserModel.id == row.user_id).first()
            if user_row is None or not user_row.is_active:
                self._repo.revoke_family(db, row.family_id)
                db.commit()
                raise InvalidRefreshTokenError("User not found or inactive")

            self._repo.mark_revoked(db, row.id)

            new_plain = secrets.token_urlsafe(48)
            new_hash = _hash_refresh_token(new_plain)
            new_expires = _utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            self._repo.add(
                db,
                user_id=row.user_id,
                token_hash=new_hash,
                family_id=row.family_id,
                expires_at=new_expires,
            )
            db.commit()

            username = user_row.username

        access_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access = create_access_token(
            data={"sub": username},
            expires_delta=access_delta,
        )
        return access, new_plain, int(access_delta.total_seconds())

    def revoke_refresh(self, refresh_plain: str) -> None:
        """Отзыв одной сессии (logout). Невалидный токен — без ошибки (идемпотентно)."""
        if not refresh_plain or not refresh_plain.strip():
            return
        th = _hash_refresh_token(refresh_plain)
        with get_db_context() as db:
            row = self._repo.get_by_token_hash(db, th)
            if row and not row.revoked:
                self._repo.mark_revoked(db, row.id)
            db.commit()


def get_token_session_service() -> TokenSessionService:
    """Заглушка для FastAPI Depends (явное внедрение зависимости)."""
    return token_session_service


token_session_service = TokenSessionService(refresh_session_repository)
