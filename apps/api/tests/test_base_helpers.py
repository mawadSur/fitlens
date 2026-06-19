"""Unit tests for agents/base.py date helpers — currently zero coverage."""
import pytest
from datetime import date, timedelta
from app.agents.base import days_until, days_on_bench


# ─── days_until ───────────────────────────────────────────────────────────────

def test_days_until_returns_none_for_none_target():
    assert days_until(None) is None


def test_days_until_future_date():
    today = date(2026, 1, 1)
    target = date(2026, 1, 11)
    assert days_until(target, today) == 10


def test_days_until_past_date_is_negative():
    today = date(2026, 1, 10)
    target = date(2026, 1, 1)
    assert days_until(target, today) == -9


def test_days_until_same_day_is_zero():
    today = date(2026, 6, 18)
    assert days_until(today, today) == 0


def test_days_until_uses_date_today_when_not_supplied():
    # Can't assert exact value; just confirm it runs and returns an int.
    result = days_until(date.today() + timedelta(days=5))
    assert isinstance(result, int)


# ─── days_on_bench ────────────────────────────────────────────────────────────

def test_days_on_bench_none_returns_zero():
    assert days_on_bench(None) == 0


def test_days_on_bench_past_start():
    today = date(2026, 6, 18)
    start = date(2026, 5, 19)
    assert days_on_bench(start, today) == 30


def test_days_on_bench_future_start_clamps_to_zero():
    today = date(2026, 6, 18)
    future = date(2026, 6, 25)
    assert days_on_bench(future, today) == 0


def test_days_on_bench_same_day_is_zero():
    today = date(2026, 6, 18)
    assert days_on_bench(today, today) == 0
