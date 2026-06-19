"""Talent-side agents: Bench Monitoring, Resume Intelligence, Immigration Compliance."""
from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..embeddings import embed_text
from ..llm import get_llm
from ..models import Consultant, ConsultantStatus, ImmigrationRecord, Resume, VisaStatus
from ..parsing import extract_skills
from .base import BaseAgent, days_on_bench, days_until

# ───────────────────────── Agent 1: Bench Monitoring ─────────────────────────


class BenchAgent(BaseAgent):
    name = "bench"
    description = "Continuously monitors consultant availability and bench cost."

    def run(self, db: Session, horizon_days: int = 30, today: date | None = None) -> dict:
        today = today or date.today()
        consultants = db.scalars(select(Consultant)).all()
        hot, alerts, total_daily = [], [], 0.0
        for c in consultants:
            d_avail = days_until(c.availability_date, today)
            benched = c.status in (ConsultantStatus.AVAILABLE, ConsultantStatus.MARKETING)
            becoming = d_avail is not None and 0 <= d_avail <= horizon_days
            if not (benched or becoming):
                continue
            dob = days_on_bench(c.bench_start_date, today) if benched else 0
            cost = c.daily_bench_cost if benched else 0.0
            total_daily += cost
            entry = {
                "consultant_id": c.id,
                "name": c.name,
                "visa_status": c.visa_status.value,
                "primary_skill": c.primary_skill,
                "status": c.status.value,
                "days_until_available": d_avail,
                "days_on_bench": dob,
                "bench_cost_accrued": round(cost * dob, 2),
                "daily_bench_cost": cost,
            }
            hot.append(entry)
            if becoming and not benched:
                alerts.append(f"{c.name} becomes available in {d_avail} days.")
            if dob >= 45:
                alerts.append(f"{c.name} has been on bench {dob} days — escalate marketing.")
        hot.sort(key=lambda e: (e["days_until_available"] is None, e["days_until_available"] or 0))
        return {
            "hot_bench": hot,
            "alerts": alerts,
            "total_daily_bench_cost": round(total_daily, 2),
            "count": len(hot),
        }


# ───────────────────────── Agent 2: Resume Intelligence ─────────────────────────


class ResumeAgent(BaseAgent):
    name = "resume"
    description = "Parses, embeds, and tailors resumes; extracts skills."

    def process_resume(self, db: Session, resume: Resume) -> Resume:
        """Ensure a resume has extracted skills + an embedding. Idempotent."""
        if not resume.parsed_skills:
            resume.parsed_skills = extract_skills(resume.content_text)
        if not resume.embedding:
            basis = resume.content_text or " ".join(resume.parsed_skills)
            resume.embedding = embed_text(basis)
        db.add(resume)
        db.commit()
        db.refresh(resume)
        return resume

    def tailor(self, db: Session, consultant_id: int, job_description: str) -> dict:
        c = db.get(Consultant, consultant_id)
        if not c:
            raise ValueError("consultant not found")
        jd_skills = set(extract_skills(job_description))
        have = set(s.lower() for s in c.skills)
        gaps = sorted(jd_skills - have)
        prompt = (
            f"Tailor a 4-line professional summary for {c.name}, a {c.primary_skill} "
            f"consultant with skills {', '.join(c.skills)}. Emphasize overlap with: "
            f"{', '.join(sorted(jd_skills)) or 'the role'}."
        )
        summary = get_llm().complete(prompt, system="FitLens Resume Intelligence Agent")
        return {
            "consultant_id": c.id,
            "tailored_summary": summary,
            "keyword_gaps": gaps,
            "ats_keywords": sorted(jd_skills & have),
        }

    def run(self, db: Session, consultant_id: int, job_description: str = "") -> dict:
        c = db.get(Consultant, consultant_id)
        if not c:
            raise ValueError("consultant not found")
        for r in c.resumes:
            self.process_resume(db, r)
        result = {"consultant_id": c.id, "skills": c.skills, "resumes": len(c.resumes)}
        if job_description:
            result["tailoring"] = self.tailor(db, consultant_id, job_description)
        return result


# ───────────────────────── Agent 3: Immigration Compliance ─────────────────────────

# Transfer/portability rules per visa type (simplified but realistic).
_TRANSFER_RULES: dict[VisaStatus, tuple[bool, str]] = {
    VisaStatus.H1B: (True, "H-1B is portable via a new H-1B transfer petition (AC21)."),
    VisaStatus.OPT: (True, "OPT employer change allowed; update SEVP within 10 days."),
    VisaStatus.STEM_OPT: (False, "STEM OPT requires E-Verify employer + new I-983 training plan."),
    VisaStatus.H4_EAD: (True, "H-4 EAD permits any employer while valid."),
    VisaStatus.L1: (False, "L-1 is employer-specific; needs H-1B/transfer to change employer."),
    VisaStatus.TN: (False, "TN is employer-specific; new petition required per employer."),
    VisaStatus.GC: (True, "Green Card — unrestricted."),
    VisaStatus.GC_EAD: (True, "GC EAD — unrestricted while valid."),
    VisaStatus.USC: (True, "U.S. Citizen — unrestricted."),
    VisaStatus.C2C: (True, "Corp-to-corp — authorization handled by the vendor entity."),
    VisaStatus.W2: (True, "W-2 — domestic employment."),
}


class ImmigrationAgent(BaseAgent):
    name = "immigration"
    description = "Validates work authorization, expirations, and transfer eligibility."

    def eligibility(self, consultant: Consultant, job_visa_reqs: list[str]) -> dict:
        reqs = {r.upper() for r in job_visa_reqs}
        ok = not reqs or consultant.visa_status.value.upper() in reqs or consultant.visa_status in (
            VisaStatus.USC,
            VisaStatus.GC,
            VisaStatus.GC_EAD,
        )
        return {"eligible": ok, "visa_status": consultant.visa_status.value}

    def run(self, db: Session, horizon_days: int = 90, today: date | None = None) -> dict:
        today = today or date.today()
        records = db.scalars(select(ImmigrationRecord)).all()
        alerts, summaries = [], []
        for rec in records:
            c = rec.consultant
            transfer_ok, reason = _TRANSFER_RULES.get(rec.visa_type, (False, "Review manually."))
            expiries = {
                "work_auth_end": days_until(rec.work_auth_end, today),
                "ead_expiry": days_until(rec.ead_expiry, today),
                "i94_expiry": days_until(rec.i94_expiry, today),
            }
            soonest = min((v for v in expiries.values() if v is not None), default=None)
            if soonest is not None and soonest <= horizon_days:
                label = "EXPIRED" if soonest < 0 else f"expires in {soonest} days"
                alerts.append(f"{c.name} ({rec.visa_type.value}) work authorization {label}.")
            summaries.append(
                {
                    "consultant_id": c.id,
                    "name": c.name,
                    "visa_type": rec.visa_type.value,
                    "transfer_eligible": transfer_ok,
                    "transfer_note": reason,
                    "lca_filed": rec.lca_filed,
                    "worksite_location": rec.worksite_location,
                    "days_to_expiry": expiries,
                }
            )
        return {"alerts": alerts, "authorizations": summaries, "count": len(summaries)}
