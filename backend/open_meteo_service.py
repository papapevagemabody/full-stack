# open_meteo_service.py — интеграция Open-Meteo (без API-ключа), лаб. №4
from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from typing import Any, Dict, Optional, Tuple

import httpx

from config import settings

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


class SimpleRateLimiter:
    """Простое ограничение: не более N запросов за скользящее окно 60 с на ключ (например IP)."""

    def __init__(self, max_per_minute: int) -> None:
        self.max_per_minute = max(1, max_per_minute)
        self._windows: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.time()
        q = self._windows[key]
        while q and q[0] < now - 60.0:
            q.popleft()
        if len(q) >= self.max_per_minute:
            return False
        q.append(now)
        return True


class OpenMeteoService:
    def __init__(self) -> None:
        self._timeout = settings.EXTERNAL_HTTP_TIMEOUT_SEC
        self._retries = max(1, settings.EXTERNAL_HTTP_MAX_RETRIES)
        self._limiter = SimpleRateLimiter(settings.WEATHER_RATE_LIMIT_PER_MINUTE)
        self._headers = {
            "User-Agent": "ImageRedactionMVP/1.0 (educational; lab4)",
            "Accept": "application/json",
        }

    def check_rate(self, client_key: str) -> bool:
        return self._limiter.allow(client_key or "anonymous")

    async def _get_json(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        last_err: Optional[Exception] = None
        async with httpx.AsyncClient(timeout=self._timeout, headers=self._headers) as client:
            for attempt in range(self._retries):
                try:
                    r = await client.get(url, params=params)
                    r.raise_for_status()
                    return r.json()
                except (httpx.HTTPError, ValueError) as e:
                    last_err = e
                    await asyncio.sleep(0.35 * (attempt + 1))
        raise last_err or RuntimeError("Open-Meteo request failed")

    async def geocode(self, name: str) -> Optional[Tuple[float, float, str, Optional[str]]]:
        """lat, lon, label, country_code"""
        data = await self._get_json(
            GEOCODE_URL,
            {"name": name.strip(), "count": 1, "language": "ru"},
        )
        results = data.get("results") or []
        if not results:
            return None
        r0 = results[0]
        lat = float(r0["latitude"])
        lon = float(r0["longitude"])
        label = r0.get("name") or name
        country = r0.get("country_code")
        return lat, lon, label, country

    async def current_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        return await self._get_json(
            FORECAST_URL,
            {
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,weather_code,wind_speed_10m",
                "wind_speed_unit": "kmh",
            },
        )

    async def weather_for_city(self, city: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Возвращает (ok, payload).
        payload при ok=False — причина для graceful degradation на клиенте.
        """
        name = (city or "").strip() or "Moscow"
        try:
            geo = await self.geocode(name)
            if not geo:
                return False, {"message": "Город не найден в геокодере Open-Meteo"}
            lat, lon, label, country = geo
            fc = await self.current_weather(lat, lon)
            cur = fc.get("current") or {}
            return True, {
                "city": label,
                "country": country,
                "latitude": lat,
                "longitude": lon,
                "temperature_c": cur.get("temperature_2m"),
                "wind_speed_kmh": cur.get("wind_speed_10m"),
                "weather_code": cur.get("weather_code"),
            }
        except Exception as e:
            return False, {"message": f"Внешний сервис недоступен: {type(e).__name__}"}


open_meteo_service = OpenMeteoService()
