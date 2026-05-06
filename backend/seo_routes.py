# seo_routes.py — лаб. №4: robots.txt, sitemap.xml, JSON-LD
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse, Response

from config import settings

router = APIRouter(tags=["seo"], include_in_schema=False)


@router.get("/robots.txt")
def robots_txt() -> Response:
    sm_url = f"{settings.sitemap_announce_url}/sitemap.xml"
    body = f"""User-agent: *
Allow: /

# Служебные и закрытые разделы SPA (не индексировать)
Disallow: /redaction
Disallow: /profile
Disallow: /catalog
Disallow: /admin/
Disallow: /login
Disallow: /register
Disallow: /status

Sitemap: {sm_url}
"""
    return Response(content=body, media_type="text/plain; charset=utf-8")


@router.get("/sitemap.xml")
def sitemap_xml() -> Response:
    base = settings.SITE_PUBLIC_URL.rstrip("/")
    # Только публичные страницы, которые должны попадать в выдачу
    entries = [
        ("", "1.0"),
        ("/about", "0.85"),
    ]
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for path, priority in entries:
        loc = f"{base}/" if path == "" else f"{base}{path}"
        parts.append("  <url>")
        parts.append(f"    <loc>{loc}</loc>")
        parts.append(f"    <priority>{priority}</priority>")
        parts.append("  </url>")
    parts.append("</urlset>")
    xml = "\n".join(parts) + "\n"
    return Response(content=xml, media_type="application/xml")


@router.get("/seo/jsonld/website")
def jsonld_website() -> JSONResponse:
    """Структурированные данные WebSite для проверки валидаторами (дублируется в React через Helmet)."""
    base = settings.SITE_PUBLIC_URL.rstrip("/")
    payload = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": settings.APP_NAME,
        "url": base,
        "description": "Сервис обнаружения и цензурирования лиц на изображениях (учебный MVP).",
        "inLanguage": "ru-RU",
    }
    return JSONResponse(content=payload)


@router.get("/lab410-demo", status_code=410, include_in_schema=True)
def lab410_demo() -> dict:
    """Демонстрация HTTP 410 Gone для исключённых из индекса ресурсов (лаб. №4)."""
    return {"detail": "Ресурс навсегда удалён (пример 410 Gone)"}
