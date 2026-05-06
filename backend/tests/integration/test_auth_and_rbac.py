"""Лаб. №5: аутентификация и защита эндпоинтов."""
from __future__ import annotations

import uuid

import pytest


@pytest.mark.integration
def test_users_me_without_token_unauthorized(client):
    r = client.get("/users/me")
    assert r.status_code == 401


@pytest.mark.integration
def test_user_assets_without_token_unauthorized(client):
    r = client.get("/user-assets")
    assert r.status_code == 401


@pytest.mark.integration
def test_token_login_demo_admin(client):
    r = client.post(
        "/token",
        data={"username": "admin", "password": "secret123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert "access_token" in data
    assert data.get("token_type") == "bearer"
    assert "refresh_token" in data


@pytest.mark.integration
def test_token_wrong_password(client):
    r = client.post(
        "/token",
        data={"username": "admin", "password": "wrong-password-xyz"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 401


@pytest.mark.integration
def test_register_validation_short_password(client):
    r = client.post(
        "/register",
        json={
            "username": f"u_{uuid.uuid4().hex[:8]}",
            "email": "a@b.c",
            "password": "123",
        },
    )
    assert r.status_code == 422


@pytest.mark.integration
def test_user_assets_list_with_admin_token(client):
    tok = client.post(
        "/token",
        data={"username": "admin", "password": "secret123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ).json()["access_token"]
    r = client.get("/user-assets", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200
    body = r.json()
    assert "items" in body
    assert "total" in body
    assert "page" in body
