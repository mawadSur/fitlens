"""Tests for SubmissionAgent, InterviewAgent, FollowupAgent — currently zero coverage."""
import pytest
from datetime import date, datetime, timezone, timedelta
from unittest.mock import patch
from app.agents.outreach import FollowupAgent, InterviewAgent, SubmissionAgent
from app.models import Consultant, Job, Submission, SubmissionStatus


def _first_consultant(db) -> Consultant:
    return db.query(Consultant).first()


def _first_open_job(db) -> Job:
    return db.query(Job).filter(Job.status == "open").first()


# ─── SubmissionAgent ──────────────────────────────────────────────────────────

def test_submission_creates_record(db):
    c = _first_consultant(db)
    j = _first_open_job(db)
    result = SubmissionAgent().submit(db, c.id, j.id)
    assert result["consultant_id"] == c.id
    assert result["job_id"] == j.id
    assert result["status"] == SubmissionStatus.SUBMITTED.value
    assert result["submission_id"] > 0
    assert "rtr" in result
    assert c.name in result["rtr"]


def test_submission_rtr_contains_job_and_rate(db):
    c = _first_consultant(db)
    j = _first_open_job(db)
    result = SubmissionAgent().submit(db, c.id, j.id, rate=85.0)
    assert "85.00" in result["rtr"]
    assert j.title in result["rtr"]


def test_submission_rate_defaults_to_band_midpoint(db):
    c = _first_consultant(db)
    j = _first_open_job(db)
    if j.min_rate and j.max_rate:
        expected = round((j.min_rate + j.max_rate) / 2, 2)
        result = SubmissionAgent().submit(db, c.id, j.id)
        assert result["rate"] == pytest.approx(expected)


def test_submission_invalid_consultant_raises(db):
    j = _first_open_job(db)
    with pytest.raises(ValueError, match="consultant or job not found"):
        SubmissionAgent().submit(db, 999999, j.id)


def test_submission_invalid_job_raises(db):
    c = _first_consultant(db)
    with pytest.raises(ValueError, match="consultant or job not found"):
        SubmissionAgent().submit(db, c.id, 999999)


def test_submission_match_score_recorded(db):
    c = _first_consultant(db)
    j = _first_open_job(db)
    result = SubmissionAgent().submit(db, c.id, j.id)
    assert 0 <= result["match_score"] <= 100


# ─── InterviewAgent ───────────────────────────────────────────────────────────

def test_next_business_slots_skips_weekends():
    agent = InterviewAgent()
    # Use a known Monday so we can predict the slots.
    monday = date(2026, 6, 22)
    slots = agent._next_business_slots(monday, n=3)
    for slot in slots:
        assert slot.weekday() < 5  # Mon-Fri only


def test_next_business_slots_returns_n_slots():
    agent = InterviewAgent()
    slots = agent._next_business_slots(date(2026, 6, 18), n=5)
    assert len(slots) == 5


def test_next_business_slots_are_utc():
    agent = InterviewAgent()
    slots = agent._next_business_slots(date(2026, 6, 18))
    for slot in slots:
        assert slot.tzinfo is not None


def test_interview_schedule_creates_record(db):
    c = _first_consultant(db)
    j = _first_open_job(db)
    sub = SubmissionAgent().submit(db, c.id, j.id)
    with patch("app.agents.outreach.get_llm") as mock_llm:
        mock_llm.return_value.complete.return_value = "Interview confirmed."
        result = InterviewAgent().schedule(db, sub["submission_id"])
    assert result["interview_id"] > 0
    assert result["submission_id"] == sub["submission_id"]
    assert len(result["proposed_slots"]) == 3
    assert "confirmation" in result


def test_interview_schedule_invalid_submission_raises(db):
    with pytest.raises(ValueError, match="submission not found"):
        InterviewAgent().schedule(db, 999999)


def test_interview_updates_submission_status(db):
    c = _first_consultant(db)
    j = _first_open_job(db)
    sub = SubmissionAgent().submit(db, c.id, j.id)
    with patch("app.agents.outreach.get_llm") as mock_llm:
        mock_llm.return_value.complete.return_value = "Confirmed."
        InterviewAgent().schedule(db, sub["submission_id"])
    updated = db.get(Submission, sub["submission_id"])
    assert updated.status == SubmissionStatus.INTERVIEW


# ─── FollowupAgent ────────────────────────────────────────────────────────────

def test_followup_run_returns_required_keys(db):
    result = FollowupAgent().run(db)
    assert "due_followups" in result
    assert "count" in result


def test_followup_due_for_day_1_submission(db):
    c = _first_consultant(db)
    j = _first_open_job(db)
    sub = SubmissionAgent().submit(db, c.id, j.id)
    # Set submitted_at to exactly 1 day ago.
    s = db.get(Submission, sub["submission_id"])
    s.submitted_at = datetime.now(timezone.utc) - timedelta(days=1)
    db.add(s)
    db.commit()
    with patch("app.agents.outreach.get_llm") as mock_llm:
        mock_llm.return_value.complete.return_value = "Day-1 follow-up."
        result = FollowupAgent().run(db)
    ids = [f["submission_id"] for f in result["due_followups"]]
    assert sub["submission_id"] in ids


def test_followup_not_due_for_non_milestone_day(db):
    c = _first_consultant(db)
    j = _first_open_job(db)
    sub = SubmissionAgent().submit(db, c.id, j.id)
    s = db.get(Submission, sub["submission_id"])
    # Day 2 is not in _FOLLOWUP_DAYS.
    s.submitted_at = datetime.now(timezone.utc) - timedelta(days=2)
    db.add(s)
    db.commit()
    result = FollowupAgent().run(db)
    ids = [f["submission_id"] for f in result["due_followups"]]
    assert sub["submission_id"] not in ids


def test_followup_count_matches_due_list(db):
    result = FollowupAgent().run(db)
    assert result["count"] == len(result["due_followups"])
