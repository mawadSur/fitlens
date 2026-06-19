"""ORM -> dict serializers for API responses (kept explicit/stable)."""
from __future__ import annotations

from .agents.base import days_on_bench, days_until
from .models import Consultant, Interview, Job, Submission, Vendor


def consultant_brief(c: Consultant) -> dict:
    return {
        "id": c.id,
        "name": c.name,
        "email": c.email,
        "visa_status": c.visa_status.value,
        "status": c.status.value,
        "primary_skill": c.primary_skill,
        "skills": c.skills,
        "years_experience": c.years_experience,
        "expected_rate": c.expected_rate,
        "location": c.location,
        "availability_date": c.availability_date.isoformat() if c.availability_date else None,
        "days_until_available": days_until(c.availability_date),
        "days_on_bench": days_on_bench(c.bench_start_date),
        "daily_bench_cost": c.daily_bench_cost,
    }


def consultant_detail(c: Consultant) -> dict:
    d = consultant_brief(c)
    d["resumes"] = [
        {"id": r.id, "filename": r.filename, "parsed_skills": r.parsed_skills,
         "is_primary": r.is_primary, "has_embedding": bool(r.embedding)}
        for r in c.resumes
    ]
    if c.immigration:
        im = c.immigration
        d["immigration"] = {
            "visa_type": im.visa_type.value,
            "work_auth_end": im.work_auth_end.isoformat() if im.work_auth_end else None,
            "ead_expiry": im.ead_expiry.isoformat() if im.ead_expiry else None,
            "i94_expiry": im.i94_expiry.isoformat() if im.i94_expiry else None,
            "lca_filed": im.lca_filed,
            "worksite_location": im.worksite_location,
        }
    return d


def job_brief(j: Job) -> dict:
    return {
        "id": j.id,
        "title": j.title,
        "client": j.client,
        "location": j.location,
        "remote": j.remote,
        "required_skills": j.required_skills,
        "rate_band": [j.min_rate, j.max_rate],
        "visa_requirements": j.visa_requirements,
        "source": j.source,
        "status": j.status,
        "vendor_id": j.vendor_id,
    }


def vendor_brief(v: Vendor) -> dict:
    return {
        "id": v.id,
        "name": v.name,
        "tier": v.tier,
        "response_rate": v.response_rate,
        "avg_response_hours": v.avg_response_hours,
        "placements_count": v.placements_count,
        "contact_email": v.contact_email,
    }


def submission_brief(s: Submission) -> dict:
    return {
        "id": s.id,
        "consultant_id": s.consultant_id,
        "consultant_name": s.consultant.name if s.consultant else None,
        "job_id": s.job_id,
        "job_title": s.job.title if s.job else None,
        "vendor_id": s.vendor_id,
        "rate": s.rate,
        "status": s.status.value,
        "match_score": s.match_score,
        "rtr_signed": s.rtr_signed,
        "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None,
    }


def interview_brief(i: Interview) -> dict:
    return {
        "id": i.id,
        "submission_id": i.submission_id,
        "scheduled_at": i.scheduled_at.isoformat() if i.scheduled_at else None,
        "mode": i.mode,
        "status": i.status,
        "panel": i.panel,
    }
