# repositories/user_asset_repository.py
from __future__ import annotations

from datetime import datetime, time, timezone
from typing import List, Optional, Tuple, Literal

from sqlalchemy import asc, desc, func, or_
from sqlalchemy.orm import Session, joinedload

from models import UserAsset

SortField = Literal["created_at", "title", "size_bytes", "original_filename"]
SortOrder = Literal["asc", "desc"]


class UserAssetRepository:
    def get_by_id(self, db: Session, asset_id: int) -> Optional[UserAsset]:
        return (
            db.query(UserAsset)
            .options(joinedload(UserAsset.owner))
            .filter(UserAsset.id == asset_id)
            .first()
        )

    def get_by_object_name(self, db: Session, object_name: str) -> Optional[UserAsset]:
        return db.query(UserAsset).filter(UserAsset.object_name == object_name).first()

    def _apply_filters(
        self,
        query,
        *,
        owner_user_id: Optional[int],
        q: Optional[str],
        category: Optional[str],
        date_from,
        date_to,
    ):
        if owner_user_id is not None:
            query = query.filter(UserAsset.user_id == owner_user_id)
        if q and q.strip():
            # lower().like() — одинаково работает в SQLite и PostgreSQL; ilike на SQLite бывает проблемным
            like = f"%{q.strip().lower()}%"
            query = query.filter(
                or_(
                    func.lower(UserAsset.title).like(like),
                    func.lower(func.coalesce(UserAsset.description, "")).like(like),
                    func.lower(UserAsset.original_filename).like(like),
                )
            )
        if category and category.strip():
            query = query.filter(UserAsset.category == category.strip())
        if date_from is not None:
            start = datetime.combine(date_from, time.min, tzinfo=timezone.utc)
            query = query.filter(UserAsset.created_at >= start)
        if date_to is not None:
            end = datetime.combine(date_to, time.max, tzinfo=timezone.utc)
            query = query.filter(UserAsset.created_at <= end)
        return query

    def list_filtered(
        self,
        db: Session,
        *,
        owner_user_id: Optional[int],
        q: Optional[str],
        category: Optional[str],
        date_from,
        date_to,
        sort_by: SortField,
        sort_order: SortOrder,
        page: int,
        page_size: int,
    ) -> Tuple[List[UserAsset], int]:
        q_count = self._apply_filters(
            db.query(UserAsset),
            owner_user_id=owner_user_id,
            q=q,
            category=category,
            date_from=date_from,
            date_to=date_to,
        )
        total = q_count.count()

        q_rows = self._apply_filters(
            db.query(UserAsset).options(joinedload(UserAsset.owner)),
            owner_user_id=owner_user_id,
            q=q,
            category=category,
            date_from=date_from,
            date_to=date_to,
        )
        col = getattr(UserAsset, sort_by)
        order_fn = asc if sort_order == "asc" else desc
        offset = (page - 1) * page_size
        rows = q_rows.order_by(order_fn(col)).offset(offset).limit(page_size).all()
        return rows, total

    def create(
        self,
        db: Session,
        *,
        user_id: int,
        title: str,
        description: Optional[str],
        category: str,
        object_name: str,
        original_filename: str,
        content_type: Optional[str],
        size_bytes: int,
    ) -> UserAsset:
        row = UserAsset(
            user_id=user_id,
            title=title,
            description=description,
            category=category,
            object_name=object_name,
            original_filename=original_filename,
            content_type=content_type,
            size_bytes=size_bytes,
        )
        db.add(row)
        db.flush()
        return row

    def save(self, db: Session, row: UserAsset) -> UserAsset:
        db.add(row)
        return row

    def delete(self, db: Session, row: UserAsset) -> None:
        db.delete(row)


user_asset_repository = UserAssetRepository()
