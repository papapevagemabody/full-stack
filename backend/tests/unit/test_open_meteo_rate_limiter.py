"""Лаб. №5: модульный тест вспомогательной логики (лимит запросов)."""
from __future__ import annotations

import time

import pytest

from open_meteo_service import SimpleRateLimiter


@pytest.mark.unit
def test_rate_limiter_allows_within_cap():
    lim = SimpleRateLimiter(3)
    assert lim.allow("a") is True
    assert lim.allow("a") is True
    assert lim.allow("a") is True
    assert lim.allow("a") is False


@pytest.mark.unit
def test_rate_limiter_resets_after_window(monkeypatch):
    t = {"v": 1000.0}

    def fake_time():
        return t["v"]

    monkeypatch.setattr(time, "time", fake_time)
    lim = SimpleRateLimiter(1)
    assert lim.allow("x") is True
    assert lim.allow("x") is False
    t["v"] += 61
    assert lim.allow("x") is True
