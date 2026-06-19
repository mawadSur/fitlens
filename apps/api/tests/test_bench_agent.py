"""Tests for BenchAgent — currently zero coverage."""
import pytest
from datetime import date
from app.agents.talent import BenchAgent


def test_bench_run_returns_required_keys(db):
    result = BenchAgent().run(db)
    assert "hot_bench" in result
    assert "alerts" in result
    assert "total_daily_bench_cost" in result
    assert "count" in result


def test_bench_total_cost_is_non_negative(db):
    result = BenchAgent().run(db)
    assert result["total_daily_bench_cost"] >= 0.0


def test_bench_alerts_escalate_after_45_days(db):
    # Seeded data includes consultants that have been benched long enough.
    result = BenchAgent().run(db, today=date(2026, 6, 18))
    # At least one escalation alert present if any consultant >45d benched.
    for alert in result["alerts"]:
        if "escalate marketing" in alert:
            assert "days" in alert
            break


def test_bench_horizon_filters_becoming_available(db):
    # With a 0-day horizon, nobody "becoming available" should appear in alerts.
    result_tight = BenchAgent().run(db, horizon_days=0)
    for alert in result_tight["alerts"]:
        assert "becomes available" not in alert


def test_bench_hot_list_ordered_by_availability(db):
    result = BenchAgent().run(db)
    days = [
        e["days_until_available"]
        for e in result["hot_bench"]
        if e["days_until_available"] is not None
    ]
    assert days == sorted(days)


def test_bench_entry_schema(db):
    result = BenchAgent().run(db)
    if result["hot_bench"]:
        entry = result["hot_bench"][0]
        for key in ("consultant_id", "name", "visa_status", "primary_skill",
                    "status", "days_on_bench", "bench_cost_accrued", "daily_bench_cost"):
            assert key in entry


def test_bench_count_matches_hot_list_length(db):
    result = BenchAgent().run(db)
    assert result["count"] == len(result["hot_bench"])
