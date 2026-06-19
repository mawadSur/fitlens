"""Edge-case coverage for scoring.py not exercised by test_scoring.py."""
import pytest
from app import scoring


# ─── skill_overlap edge cases ─────────────────────────────────────────────────

def test_skill_overlap_both_empty():
    # Both lists empty: job has no requirements → neutral 0.5.
    assert scoring.skill_overlap([], []) == 0.5


def test_skill_overlap_case_insensitive_matching():
    assert scoring.skill_overlap(["PYTHON", "AWS"], ["python", "aws"]) == 1.0


def test_skill_overlap_whitespace_stripped():
    assert scoring.skill_overlap([" python "], ["python"]) == 1.0


def test_skill_overlap_no_job_skills_neutral():
    # Job has no stated requirements → 0.5 regardless of consultant skills.
    assert scoring.skill_overlap(["python", "spark"], []) == 0.5


def test_skill_overlap_zero_match():
    assert scoring.skill_overlap(["rust", "go"], ["python", "java"]) == 0.0


# ─── rate_fit edge cases ──────────────────────────────────────────────────────

def test_rate_fit_unknown_rate_zero_returns_neutral():
    assert scoring.rate_fit(0, 70, 95) == pytest.approx(0.6)


def test_rate_fit_unknown_band_both_zero_returns_neutral():
    assert scoring.rate_fit(80, 0, 0) == pytest.approx(0.6)


def test_rate_fit_below_band_decays():
    result = scoring.rate_fit(50, 70, 95)
    assert 0.0 <= result < 1.0


def test_rate_fit_above_band_decays():
    result = scoring.rate_fit(120, 70, 95)
    assert 0.0 <= result < 1.0


def test_rate_fit_clamps_to_zero():
    # Extremely far outside band → floor at 0.
    result = scoring.rate_fit(1000, 70, 95)
    assert result == 0.0


def test_rate_fit_max_only_band():
    # Only max supplied; min defaults to 0.
    result = scoring.rate_fit(80, 0, 95)
    assert 0.0 <= result <= 1.0


# ─── visa_allows edge cases ───────────────────────────────────────────────────

def test_visa_allows_gc_ead_with_restrictions():
    # GC_EAD should be treated as unrestricted.
    assert scoring.visa_allows("GC_EAD", ["H1B", "GC"]) is True


def test_visa_allows_gc_unrestricted():
    assert scoring.visa_allows("GC", ["H1B"]) is True


def test_visa_allows_opt_rejected_without_match():
    assert scoring.visa_allows("OPT", ["H1B", "GC"]) is False


def test_visa_allows_no_requirements_always_true():
    assert scoring.visa_allows("TN", []) is True


# ─── composite_match boundaries ───────────────────────────────────────────────

def test_composite_match_perfect_inputs_under_100():
    score = scoring.composite_match(1.0, 1.0, 1.0, visa_ok=True)
    assert 0 <= score <= 100


def test_composite_match_worst_inputs_non_negative():
    score = scoring.composite_match(-1.0, 0.0, 0.0, visa_ok=False)
    assert score >= 0.0


def test_composite_match_visa_penalty_is_25_pct():
    ok = scoring.composite_match(0.5, 0.5, 0.5, visa_ok=True)
    bad = scoring.composite_match(0.5, 0.5, 0.5, visa_ok=False)
    assert bad == round(ok * 0.25, 1)


# ─── probability caps ─────────────────────────────────────────────────────────

def test_interview_probability_capped_at_0_98():
    p = scoring.interview_probability(100, 100)
    assert p <= 0.98


def test_interview_probability_zero_vendor_defaults_to_50():
    p_zero = scoring.interview_probability(80, 0)
    p_fifty = scoring.interview_probability(80, 50)
    assert p_zero == p_fifty


def test_placement_probability_capped_at_0_97():
    p = scoring.placement_probability(100, 100, 100, active_interviews=10, days_on_bench=0)
    assert p <= 0.97


def test_placement_probability_floor_at_zero():
    p = scoring.placement_probability(0, 0, 0, active_interviews=0, days_on_bench=3000)
    assert p >= 0.0


def test_placement_probability_long_bench_penalty():
    p_fresh = scoring.placement_probability(70, 70, 70, active_interviews=0, days_on_bench=0)
    p_stale = scoring.placement_probability(70, 70, 70, active_interviews=0, days_on_bench=200)
    assert p_fresh > p_stale


def test_placement_probability_interview_boost():
    p_no = scoring.placement_probability(60, 60, 60, active_interviews=0, days_on_bench=0)
    p_yes = scoring.placement_probability(60, 60, 60, active_interviews=3, days_on_bench=0)
    assert p_yes > p_no
