"""Лаб. №5: базовые ответы API."""
from __future__ import annotations

import pytest


@pytest.mark.integration
def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert "status" in body


@pytest.mark.integration
def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "message" in r.json()
