"""Лаб. №5: модульный тест репозитория на изолированной SQLite (без запуска всего app)."""
from __future__ import annotations


import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models import Base, User, UserAsset
from repositories.user_asset_repository import UserAssetRepository


@pytest.mark.unit
def test_list_filtered_search_and_pagination():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    u = User(username="tuser", email="t@t.t", password_hash="x", is_active=True)
    db.add(u)
    db.commit()
    db.refresh(u)

    repo = UserAssetRepository()
    for i in range(5):
        db.add(
            UserAsset(
                user_id=u.id,
                title=f"Photo {i}",
                description=None,
                category="upload",
                object_name=f"tuser/assets/{i}.bin",
                original_filename=f"f{i}.jpg",
                content_type="image/jpeg",
                size_bytes=100 + i,
            )
        )
    db.commit()

    rows, total = repo.list_filtered(
        db,
        owner_user_id=u.id,
        q="photo",
        category=None,
        date_from=None,
        date_to=None,
        sort_by="title",
        sort_order="asc",
        page=1,
        page_size=2,
    )
    assert total >= 5
    assert len(rows) == 2

    rows2, _ = repo.list_filtered(
        db,
        owner_user_id=u.id,
        q=None,
        category="upload",
        date_from=None,
        date_to=None,
        sort_by="created_at",
        sort_order="desc",
        page=1,
        page_size=10,
    )
    assert len(rows2) == 5

    db.close()
