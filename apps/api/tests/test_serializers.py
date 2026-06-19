"""Tests for serializers.py — currently zero coverage."""
import pytest
from datetime import date, datetime, timezone
from unittest.mock import MagicMock
from app.serializers import (
    consultant_brief,
    consultant_detail,
    interview_brief,
    job_brief,
    submission_brief,
    vendor_brief,
)
from app.models import (
    Consultant, ConsultantStatus, Interview, Job, Submission,
    SubmissionStatus, Vendor, VisaStatus,
)


def _mock_consultant(**kw):
    c = MagicMock(spec=Consultant)
    c.id = 1
    c.name = "Alice"
    c.email = "alice@example.com"
    c.visa_status = VisaStatus.H1B
    c.status = ConsultantStatus.AVAILABLE
    c.primary_skill = "Python"
    c.skills = ["python", "aws"]
    c.years_experience = 5.0
    c.expected_rate = 90.0
    c.location = "Austin, TX"
    c.availability_date = None
    c.bench_start_date = None
    c.daily_bench_cost = 200.0
    c.resumes = []
    c.immigration = None
    for k, v in kw.items():
        setattr(c, k, v)
    return c


# ─── consultant_brief ─────────────────────────────────────────────────────────

def test_consultant_brief_has_all_keys():
    c = _mock_consultant()
    result = consultant_brief(c)
    for key in ("id", "name", "email", "visa_status", "status", "primary_skill",
                "skills", "years_experience", "expected_rate", "location",
                "availability_date", "days_until_available", "days_on_bench",
                "daily_bench_cost"):
        assert key in result


def test_consultant_brief_availability_date_iso():
    c = _mock_consultant(availability_date=date(2026, 9, 1))
    result = consultant_brief(c)
    assert result["availability_date"] == "2026-09-01"


def test_consultant_brief_no_availability_is_none():
    c = _mock_consultant(availability_date=None)
    result = consultant_brief(c)
    assert result["availability_date"] is None


# ─── consultant_detail ────────────────────────────────────────────────────────

def test_consultant_detail_includes_resumes_list():
    c = _mock_consultant()
    result = consultant_detail(c)
    assert "resumes" in result
    assert isinstance(result["resumes"], list)


def test_consultant_detail_no_immigration_key_absent():
    c = _mock_consultant(immigration=None)
    result = consultant_detail(c)
    assert "immigration" not in result


def test_consultant_detail_with_immigration():
    im = MagicMock()
    im.visa_type = VisaStatus.H1B
    im.work_auth_end = date(2027, 1, 1)
    im.ead_expiry = None
    im.i94_expiry = None
    im.lca_filed = True
    im.worksite_location = "Austin, TX"
    c = _mock_consultant(immigration=im)
    result = consultant_detail(c)
    assert "immigration" in result
    assert result["immigration"]["lca_filed"] is True


# ─── job_brief ────────────────────────────────────────────────────────────────

def test_job_brief_has_all_keys():
    j = MagicMock(spec=Job)
    j.id = 1
    j.title = "Senior Python Dev"
    j.client = "Acme"
    j.location = "Remote"
    j.remote = True
    j.required_skills = ["python"]
    j.min_rate = 80.0
    j.max_rate = 120.0
    j.visa_requirements = []
    j.source = "direct"
    j.status = "open"
    j.vendor_id = None
    result = job_brief(j)
    for key in ("id", "title", "client", "location", "remote",
                "required_skills", "rate_band", "visa_requirements",
                "source", "status", "vendor_id"):
        assert key in result


def test_job_brief_rate_band_is_list():
    j = MagicMock(spec=Job)
    j.id = 1; j.title = "Dev"; j.client = "X"; j.location = ""; j.remote = False
    j.required_skills = []; j.min_rate = 70.0; j.max_rate = 100.0
    j.visa_requirements = []; j.source = "manual"; j.status = "open"; j.vendor_id = None
    result = job_brief(j)
    assert result["rate_band"] == [70.0, 100.0]


# ─── vendor_brief ─────────────────────────────────────────────────────────────

def test_vendor_brief_has_all_keys():
    v = MagicMock(spec=Vendor)
    v.id = 1; v.name = "Infosys"; v.tier = "A"; v.response_rate = 0.9
    v.avg_response_hours = 12.0; v.placements_count = 10; v.contact_email = "a@b.com"
    result = vendor_brief(v)
    for key in ("id", "name", "tier", "response_rate",
                "avg_response_hours", "placements_count", "contact_email"):
        assert key in result


# ─── submission_brief ─────────────────────────────────────────────────────────

def test_submission_brief_has_all_keys():
    s = MagicMock(spec=Submission)
    s.id = 1; s.consultant_id = 1; s.job_id = 1; s.vendor_id = None
    s.rate = 85.0; s.status = SubmissionStatus.SUBMITTED
    s.match_score = 72.5; s.rtr_signed = False
    s.submitted_at = datetime(2026, 6, 1, tzinfo=timezone.utc)
    s.consultant = MagicMock(name="Alice"); s.consultant.name = "Alice"
    s.job = MagicMock(); s.job.title = "Dev Role"
    result = submission_brief(s)
    for key in ("id", "consultant_id", "job_id", "vendor_id", "rate",
                "status", "match_score", "rtr_signed", "submitted_at",
                "consultant_name", "job_title"):
        assert key in result


def test_submission_brief_submitted_at_iso():
    s = MagicMock(spec=Submission)
    s.id = 1; s.consultant_id = 1; s.job_id = 1; s.vendor_id = None
    s.rate = 85.0; s.status = SubmissionStatus.SUBMITTED
    s.match_score = 72.5; s.rtr_signed = False
    s.submitted_at = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
    s.consultant = MagicMock(); s.consultant.name = "Alice"
    s.job = MagicMock(); s.job.title = "Dev"
    result = submission_brief(s)
    assert "2026-06-01" in result["submitted_at"]


def test_submission_brief_no_submitted_at():
    s = MagicMock(spec=Submission)
    s.id = 1; s.consultant_id = 1; s.job_id = 1; s.vendor_id = None
    s.rate = 85.0; s.status = SubmissionStatus.DRAFT
    s.match_score = 0.0; s.rtr_signed = False; s.submitted_at = None
    s.consultant = MagicMock(); s.consultant.name = "Alice"
    s.job = MagicMock(); s.job.title = "Dev"
    result = submission_brief(s)
    assert result["submitted_at"] is None


# ─── interview_brief ──────────────────────────────────────────────────────────

def test_interview_brief_has_all_keys():
    i = MagicMock(spec=Interview)
    i.id = 1; i.submission_id = 1
    i.scheduled_at = datetime(2026, 7, 1, 15, 0, tzinfo=timezone.utc)
    i.mode = "video"; i.status = "proposed"; i.panel = "HM"
    result = interview_brief(i)
    for key in ("id", "submission_id", "scheduled_at", "mode", "status", "panel"):
        assert key in result


def test_interview_brief_no_scheduled_at():
    i = MagicMock(spec=Interview)
    i.id = 1; i.submission_id = 1; i.scheduled_at = None
    i.mode = "video"; i.status = "proposed"; i.panel = "HM"
    result = interview_brief(i)
    assert result["scheduled_at"] is None
