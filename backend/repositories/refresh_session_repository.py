# repositories/refresh_session_repository.py
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from models import RefreshSession


class RefreshSessionRepository:
    """Доступ к записям refresh-сессий (храним только хеш токена)."""

    def get_by_token_hash(self, db: Session, token_hash: str) -> Optional[RefreshSession]:
        return (
            db.query(RefreshSession)
            .filter(RefreshSession.token_hash == token_hash)
            .first()
        )

    def add(
        self,
        db: Session,
        *,
        user_id: int,
        token_hash: str,
        family_id: str,
        expires_at: datetime,
    ) -> RefreshSession:
        row = RefreshSession(
            user_id=user_id,
            token_hash=token_hash,
            family_id=family_id,
            revoked=False,
            expires_at=expires_at,
        )
        db.add(row)
        return row

    def mark_revoked(self, db: Session, session_id: int) -> None:
        row = db.query(RefreshSession).filter(RefreshSession.id == session_id).first()
        if row:
            row.revoked = True

    def revoke_family(self, db: Session, family_id: str) -> None:
        db.query(RefreshSession).filter(RefreshSession.family_id == family_id).update(
            {RefreshSession.revoked: True},
            synchronize_session=False,
        )


refresh_session_repository = RefreshSessionRepository()
