# conftest.py — лаб. №5: окружение test до импорта приложения
from __future__ import annotations

import os

# Важно: до import app, чтобы Settings() подхватил тестовую БД
os.environ["APP_ENV"] = "test"

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Один клиент на сессию: один раз lifespan, общая in-memory SQLite (StaticPool)."""
    from app import app

    with TestClient(app) as c:
        yield c
