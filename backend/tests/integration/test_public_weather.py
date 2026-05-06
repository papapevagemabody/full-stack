"""Лаб. №5: сторонний API — мок сервиса, структура ответа, деградация."""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from open_meteo_service import open_meteo_service


@pytest.mark.integration
def test_public_weather_success_mocked(client, monkeypatch):
    monkeypatch.setattr(
        open_meteo_service,
        "weather_for_city",
        AsyncMock(
            return_value=(
                True,
                {
                    "city": "MockCity",
                    "country": "RU",
                    "latitude": 55.0,
                    "longitude": 37.0,
                    "temperature_c": 10.5,
                    "wind_speed_kmh": 20.0,
                    "weather_code": 0,
                },
            )
        ),
    )
    monkeypatch.setattr(open_meteo_service, "check_rate", lambda _ip: True)

    r = client.get("/public/weather?city=MockCity")
    assert r.status_code == 200
    data = r.json()
    assert data["available"] is True
    assert data["city"] == "MockCity"
    assert data["temperature_c"] == 10.5
    assert data["provider"] == "open-meteo"


@pytest.mark.integration
def test_public_weather_graceful_degradation_mocked(client, monkeypatch):
    monkeypatch.setattr(
        open_meteo_service,
        "weather_for_city",
        AsyncMock(return_value=(False, {"message": "Внешний сбой"})),
    )
    monkeypatch.setattr(open_meteo_service, "check_rate", lambda _ip: True)

    r = client.get("/public/weather?city=Any")
    assert r.status_code == 200
    data = r.json()
    assert data["available"] is False
    assert data.get("message")


@pytest.mark.integration
def test_public_weather_rate_limited_mocked(client, monkeypatch):
    monkeypatch.setattr(open_meteo_service, "check_rate", lambda _ip: False)
    r = client.get("/public/weather?city=Moscow")
    assert r.status_code == 200
    assert r.json()["available"] is False
    assert "лимит" in (r.json().get("message") or "").lower()
