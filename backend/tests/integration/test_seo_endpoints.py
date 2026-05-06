"""Лаб. №5: SEO-эндпоинты, коды ответа и формат."""
from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest


@pytest.mark.integration
def test_robots_txt_ok(client):
    r = client.get("/robots.txt")
    assert r.status_code == 200
    assert "User-agent" in r.text
    assert "Sitemap:" in r.text
    assert "Disallow: /profile" in r.text


@pytest.mark.integration
def test_sitemap_xml_ok(client):
    r = client.get("/sitemap.xml")
    assert r.status_code == 200
    root = ET.fromstring(r.content)
    assert root.tag.endswith("urlset")
    locs = [e.text for e in root.iter() if e.tag.endswith("loc")]
    assert any(loc.endswith("/") or loc.endswith("localhost:3000/") for loc in locs)


@pytest.mark.integration
def test_jsonld_website(client):
    r = client.get("/seo/jsonld/website")
    assert r.status_code == 200
    data = r.json()
    assert data.get("@type") == "WebSite"
    assert "url" in data


@pytest.mark.integration
def test_lab410_gone(client):
    r = client.get("/lab410-demo")
    assert r.status_code == 410
