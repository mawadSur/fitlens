"""Unit tests for the pure scoring engine."""
from app import scoring
from app.embeddings.base import cosine_similarity


def test_skill_overlap_full_and_partial():
    assert scoring.skill_overlap(["Python", "AWS"], ["python", "aws"]) == 1.0
    assert scoring.skill_overlap(["python"], ["python", "aws"]) == 0.5
    assert scoring.skill_overlap([], ["python"]) == 0.0
    assert scoring.skill_overlap(["python"], []) == 0.5  # no requirement => neutral


def test_rate_fit_inside_and_outside_band():
    assert scoring.rate_fit(80, 70, 95) == 1.0
    assert scoring.rate_fit(120, 70, 95) < 1.0
    assert scoring.rate_fit(120, 70, 95) >= 0.0


def test_visa_allows():
    assert scoring.visa_allows("H1B", []) is True            # no restriction
    assert scoring.visa_allows("H1B", ["H1B", "GC"]) is True
    assert scoring.visa_allows("OPT", ["H1B", "GC"]) is False
    assert scoring.visa_allows("USC", ["H1B"]) is True        # citizen always ok


def test_composite_match_visa_penalty():
    ok = scoring.composite_match(0.8, 1.0, 1.0, visa_ok=True)
    bad = scoring.composite_match(0.8, 1.0, 1.0, visa_ok=False)
    assert ok > bad
    assert bad == round(ok * 0.25, 1)
    assert 0 <= ok <= 100


def test_probabilities_monotonic():
    low = scoring.interview_probability(40, 50)
    high = scoring.interview_probability(90, 80)
    assert high > low
    assert 0 <= low <= 1 and 0 <= high <= 1

    p_more = scoring.placement_probability(90, 80, 80, active_interviews=2, days_on_bench=5)
    p_less = scoring.placement_probability(40, 40, 40, active_interviews=0, days_on_bench=120)
    assert p_more > p_less


def test_cosine_similarity():
    assert cosine_similarity([1, 0], [1, 0]) == 1.0
    assert abs(cosine_similarity([1, 0], [0, 1])) < 1e-6
    assert cosine_similarity([1, 0], []) == 0.0
