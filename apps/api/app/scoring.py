"""Deterministic scoring engine shared by the Matching/Placement/Revenue agents.

All functions are pure and unit-tested. Weights are explicit so they can be tuned
or, later, learned from placement outcomes.
"""
from __future__ import annotations

from typing import Iterable

# Visa types that carry their own unrestricted work authorization.
_ALWAYS_ELIGIBLE = {"USC", "GC", "GC_EAD"}


def _norm(s: str) -> str:
    return s.strip().lower()


def skill_set(skills: Iterable[str]) -> set[str]:
    return {_norm(s) for s in skills if s and s.strip()}


def skill_overlap(consultant_skills: Iterable[str], job_skills: Iterable[str]) -> float:
    """Fraction of the job's required skills the consultant covers (0..1)."""
    job = skill_set(job_skills)
    if not job:
        return 0.5  # no stated requirements => neutral
    cons = skill_set(consultant_skills)
    return len(job & cons) / len(job)


def rate_fit(expected_rate: float, job_min: float, job_max: float) -> float:
    """1.0 when the consultant's expected rate sits inside the job band, decaying
    smoothly as it falls outside it."""
    if not expected_rate or (not job_min and not job_max):
        return 0.6  # unknown => mildly positive
    lo, hi = (job_min or 0.0), (job_max or job_min or expected_rate)
    if lo <= expected_rate <= hi:
        return 1.0
    band = max(hi - lo, 1.0)
    distance = (lo - expected_rate) if expected_rate < lo else (expected_rate - hi)
    return max(0.0, 1.0 - distance / band)


def visa_allows(consultant_visa: str, job_visa_reqs: Iterable[str]) -> bool:
    cv = consultant_visa.strip().upper()
    if cv in _ALWAYS_ELIGIBLE:
        return True  # citizens / green-card holders are universally work-authorized
    reqs = {r.strip().upper() for r in job_visa_reqs if r}
    if not reqs:
        return True  # no restriction stated
    if cv in reqs:
        return True
    return bool({"ANY", "ALL", "ALL VISAS"} & reqs)


def composite_match(
    semantic: float, skill: float, rate: float, visa_ok: bool
) -> float:
    """Blend signals into a 0..100 match score. Visa ineligibility is a hard
    penalty (multiplies by 0.25) rather than a zero, so recruiters still see
    near-misses worth a transfer conversation."""
    semantic01 = max(0.0, min(1.0, (semantic + 1) / 2))  # cosine [-1,1] -> [0,1]
    base = 0.45 * semantic01 + 0.40 * skill + 0.15 * rate
    if not visa_ok:
        base *= 0.25
    return round(base * 100, 1)


def interview_probability(match_score: float, vendor_score: float) -> float:
    """0..1 — chance a submission converts to an interview."""
    m = match_score / 100.0
    v = (vendor_score or 50.0) / 100.0
    return round(min(0.98, 0.15 + 0.6 * m * (0.5 + 0.5 * v)), 3)


def placement_probability(
    match_score: float,
    vendor_score: float,
    demand_score: float,
    active_interviews: int,
    days_on_bench: int,
) -> float:
    """0..1 — chance of placement, factoring demand, vendor quality and momentum."""
    m = match_score / 100.0
    v = (vendor_score or 50.0) / 100.0
    d = (demand_score or 50.0) / 100.0
    interview_boost = min(0.25, 0.12 * active_interviews)
    # long bench tenure slightly lowers probability (stale profile / market signal)
    bench_penalty = min(0.20, max(0, days_on_bench - 30) / 300.0)
    p = 0.10 + 0.45 * m + 0.20 * v + 0.15 * d + interview_boost - bench_penalty
    return round(max(0.0, min(0.97, p)), 3)
