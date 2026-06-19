"""Tests for PlacementAgent and RevenueAgent — currently zero coverage."""
import pytest
from app.agents.analytics import PlacementAgent, RevenueAgent
from app.models import Consultant


def _first_consultant(db) -> Consultant:
    return db.query(Consultant).first()


# ─── PlacementAgent ───────────────────────────────────────────────────────────

def test_placement_predict_schema(db):
    c = _first_consultant(db)
    result = PlacementAgent().predict(db, c)
    for key in ("consultant_id", "name", "best_match_score", "best_job",
                "active_interviews", "days_on_bench",
                "placement_probability", "forecast"):
        assert key in result


def test_placement_probability_between_0_and_1(db):
    c = _first_consultant(db)
    result = PlacementAgent().predict(db, c)
    assert 0.0 <= result["placement_probability"] <= 1.0


def test_placement_run_all_returns_list(db):
    result = PlacementAgent().run(db)
    assert "predictions" in result
    assert "count" in result
    assert result["count"] == len(result["predictions"])


def test_placement_run_all_sorted_descending(db):
    result = PlacementAgent().run(db)
    probs = [p["placement_probability"] for p in result["predictions"]]
    assert probs == sorted(probs, reverse=True)


def test_placement_run_by_id(db):
    c = _first_consultant(db)
    result = PlacementAgent().run(db, consultant_id=c.id)
    assert result["consultant_id"] == c.id
    assert "placement_probability" in result


def test_placement_run_invalid_id_raises(db):
    with pytest.raises(ValueError, match="consultant not found"):
        PlacementAgent().run(db, consultant_id=999999)


def test_placement_forecast_string_contains_probability(db):
    c = _first_consultant(db)
    result = PlacementAgent().predict(db, c)
    assert "%" in result["forecast"]
    assert "probability" in result["forecast"]


# ─── RevenueAgent ─────────────────────────────────────────────────────────────

def test_revenue_run_returns_required_keys(db):
    result = RevenueAgent().run(db)
    for key in ("expected_placements_30d", "expected_monthly_revenue",
                "expected_gross_margin", "gross_margin_pct",
                "bench_burn_daily", "bench_burn_monthly",
                "consultants_marketed", "placements_to_date"):
        assert key in result


def test_revenue_non_negative_values(db):
    result = RevenueAgent().run(db)
    assert result["expected_placements_30d"] >= 0
    assert result["expected_monthly_revenue"] >= 0
    assert result["bench_burn_daily"] >= 0


def test_revenue_custom_gross_margin(db):
    default = RevenueAgent().run(db)
    custom = RevenueAgent().run(db, gross_margin=0.30)
    assert custom["gross_margin_pct"] == 0.30
    # Higher margin → higher gross margin dollars (revenue unchanged).
    assert custom["expected_gross_margin"] >= default["expected_gross_margin"]


def test_revenue_bench_burn_monthly_is_30x_daily(db):
    result = RevenueAgent().run(db)
    assert result["bench_burn_monthly"] == pytest.approx(result["bench_burn_daily"] * 30, rel=1e-3)
