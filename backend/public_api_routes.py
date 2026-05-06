# public_api_routes.py — лаб. №4: публичные интеграции (без JWT)
from __future__ import annotations

from fastapi import APIRouter, Query, Request

from open_meteo_service import open_meteo_service
from schemas import PublicWeatherResponse

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/weather", response_model=PublicWeatherResponse)
async def public_weather(
    request: Request,
    city: str = Query("Москва", max_length=80, description="Название города для Open-Meteo Geocoding"),
) -> PublicWeatherResponse:
    """
    Погода через Open-Meteo (геокодинг + текущие значения).
    Таймауты и повторы — в OpenMeteoService; ограничение частоты — по IP клиента.
    """
    client_ip = request.client.host if request.client else "anonymous"
    if not open_meteo_service.check_rate(client_ip):
        return PublicWeatherResponse(
            available=False,
            city=city.strip() or "Москва",
            message="Превышен лимит запросов к внешнему API. Повторите через минуту.",
        )

    ok, data = await open_meteo_service.weather_for_city(city)
    if not ok:
        return PublicWeatherResponse(
            available=False,
            city=city.strip() or "Москва",
            message=data.get("message"),
        )

    return PublicWeatherResponse(
        available=True,
        city=data["city"],
        country=data.get("country"),
        latitude=data["latitude"],
        longitude=data["longitude"],
        temperature_c=data.get("temperature_c"),
        wind_speed_kmh=data.get("wind_speed_kmh"),
        weather_code=data.get("weather_code"),
        provider="open-meteo",
    )
