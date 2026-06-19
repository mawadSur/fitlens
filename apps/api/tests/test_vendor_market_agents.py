"""Tests for VendorAgent, MarketAgent, and score_vendor — currently zero coverage."""
import pytest
from app.agents.matching import MarketAgent, VendorAgent, score_vendor
from app.models import Vendor


# ─── score_vendor ─────────────────────────────────────────────────────────────

def _make_vendor(**kw) -> Vendor:
    defaults = dict(
        id=0, name="Test", tier="B", response_rate=0.5,
        avg_response_hours=24.0, placements_count=5, score=0.0,
    )
    defaults.update(kw)
    v = Vendor.__new__(Vendor)
    v.__dict__.update(defaults)
    return v


def test_score_vendor_tier_a_bonus():
    a = _make_vendor(tier="A", response_rate=1.0, avg_response_hours=0, placements_count=20)
    b = _make_vendor(tier="B", response_rate=1.0, avg_response_hours=0, placements_count=20)
    assert score_vendor(a) > score_vendor(b)


def test_score_vendor_tier_c_no_bonus():
    c = _make_vendor(tier="C", response_rate=0.0, avg_response_hours=96, placements_count=0)
    assert score_vendor(c) == 0.0


def test_score_vendor_capped_at_100():
    v = _make_vendor(tier="A", response_rate=1.0, avg_response_hours=0, placements_count=100)
    assert score_vendor(v) <= 100.0


def test_score_vendor_fast_response_raises_score():
    fast = _make_vendor(avg_response_hours=1)
    slow = _make_vendor(avg_response_hours=96)
    assert score_vendor(fast) > score_vendor(slow)


def test_score_vendor_more_placements_raises_score():
    few = _make_vendor(placements_count=0)
    many = _make_vendor(placements_count=20)
    assert score_vendor(many) > score_vendor(few)


# ─── VendorAgent ──────────────────────────────────────────────────────────────

def test_vendor_agent_returns_required_keys(db):
    result = VendorAgent().run(db)
    assert "top_vendors" in result
    assert "count" in result


def test_vendor_agent_scores_descending(db):
    result = VendorAgent().run(db)
    scores = [v["score"] for v in result["top_vendors"]]
    assert scores == sorted(scores, reverse=True)


def test_vendor_agent_top_k_respected(db):
    result = VendorAgent().run(db, top_k=2)
    assert len(result["top_vendors"]) <= 2


def test_vendor_agent_entry_schema(db):
    result = VendorAgent().run(db)
    if result["top_vendors"]:
        v = result["top_vendors"][0]
        for key in ("vendor_id", "name", "tier", "score",
                    "response_rate", "avg_response_hours", "placements"):
            assert key in v


# ─── MarketAgent ──────────────────────────────────────────────────────────────

def test_market_agent_run_all_returns_top_skills(db):
    result = MarketAgent().run(db)
    assert "top_skills" in result
    assert isinstance(result["top_skills"], list)


def test_market_agent_run_with_skill(db):
    result = MarketAgent().run(db, skill="python")
    assert result["skill"].lower() == "python"
    assert "demand_score" in result
    assert "open_jobs" in result
    assert "recommended_rate" in result


def test_market_agent_unknown_skill_returns_default_rate(db):
    result = MarketAgent().run(db, skill="cobol_assembly_x99")
    assert result["recommended_rate"]["min"] == 55.0
    assert result["recommended_rate"]["max"] == 90.0


def test_market_agent_demand_for_known_skill_in_jobs(db):
    result = MarketAgent().demand_for(db, "databricks")
    assert result["open_jobs"] >= 0
    assert 0 <= result["demand_score"] <= 100


def test_market_agent_no_skill_top_skills_descending(db):
    result = MarketAgent().run(db)
    scores = [s["demand_score"] for s in result["top_skills"]]
    assert scores == sorted(scores, reverse=True)
