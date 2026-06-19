"""Outreach agents: Marketing, Submission, Follow-up, Interview Coordinator."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..connectors import get_email_connector
from ..llm import get_llm
from ..models import Consultant, Interview, Job, Submission, SubmissionStatus, Vendor
from .base import BaseAgent
from .matching import MatchingAgent

# ───────────────────────── Agent 7: Marketing ─────────────────────────


class MarketingAgent(BaseAgent):
    name = "marketing"
    description = "Generates hotlists and marketing outreach copy."

    def run(self, db: Session, consultant_id: int) -> dict:
        c = db.get(Consultant, consultant_id)
        if not c:
            raise ValueError("consultant not found")
        skills = ", ".join(c.skills[:8])
        hotlist = f"{c.primary_skill} | {c.visa_status.value} | {c.years_experience:.0f}y | {c.location} | ${c.expected_rate:.0f}/hr"
        email = get_llm().complete(
            f"Write a concise vendor marketing email for {c.name}, a {c.primary_skill} "
            f"consultant ({c.visa_status.value}) with skills: {skills}. Include availability and rate.",
            system="FitLens Marketing Agent",
        )
        linkedin = get_llm().complete(
            f"Write a 2-sentence LinkedIn message marketing {c.name} ({c.primary_skill}).",
            system="FitLens Marketing Agent",
        )
        return {
            "consultant_id": c.id,
            "hotlist_line": hotlist,
            "marketing_email": email,
            "linkedin_message": linkedin,
        }


# ───────────────────────── Agent 8: Submission ─────────────────────────


class SubmissionAgent(BaseAgent):
    name = "submission"
    description = "Automates the submission workflow incl. rate + RTR generation."

    def submit(
        self,
        db: Session,
        consultant_id: int,
        job_id: int,
        vendor_id: int | None = None,
        rate: float | None = None,
    ) -> dict:
        c = db.get(Consultant, consultant_id)
        j = db.get(Job, job_id)
        if not c or not j:
            raise ValueError("consultant or job not found")
        breakdown = MatchingAgent()._breakdown(c, j, semantic=0.0)
        if rate is None:
            band_mid = (j.min_rate + j.max_rate) / 2 if (j.min_rate or j.max_rate) else c.expected_rate
            rate = round(band_mid or c.expected_rate, 2)
        vendor_id = vendor_id or j.vendor_id
        sub = Submission(
            consultant_id=c.id,
            job_id=j.id,
            vendor_id=vendor_id,
            rate=rate,
            status=SubmissionStatus.SUBMITTED,
            match_score=breakdown["match_score"],
            rtr_signed=False,
            submitted_at=datetime.now(timezone.utc),
        )
        db.add(sub)
        db.commit()
        db.refresh(sub)
        rtr = (
            f"RIGHT TO REPRESENT\n\nConsultant: {c.name}\nRole: {j.title} ({j.client})\n"
            f"Bill rate: ${rate:.2f}/hr\nWork authorization: {c.visa_status.value}\n"
            f"This authorizes representation of the above consultant for the above requirement."
        )
        return {
            "submission_id": sub.id,
            "consultant_id": c.id,
            "job_id": j.id,
            "vendor_id": vendor_id,
            "rate": rate,
            "match_score": breakdown["match_score"],
            "status": sub.status.value,
            "rtr": rtr,
        }

    def run(self, db: Session, consultant_id: int, job_id: int, **kw) -> dict:
        return self.submit(db, consultant_id, job_id, **kw)


# ───────────────────────── Agent 9: Follow-up ─────────────────────────

_FOLLOWUP_DAYS = [1, 3, 5, 7, 14]


class FollowupAgent(BaseAgent):
    name = "followup"
    description = "Schedules and drafts cadenced follow-ups on open submissions."

    def run(self, db: Session, now: datetime | None = None, send: bool = False) -> dict:
        now = now or datetime.now(timezone.utc)
        active = db.scalars(
            select(Submission).where(
                Submission.status.in_(
                    [SubmissionStatus.SUBMITTED, SubmissionStatus.SHORTLISTED, SubmissionStatus.INTERVIEW]
                )
            )
        ).all()
        due = []
        for s in active:
            if not s.submitted_at:
                continue
            submitted = s.submitted_at
            if submitted.tzinfo is None:
                submitted = submitted.replace(tzinfo=timezone.utc)
            elapsed = (now - submitted).days
            if elapsed in _FOLLOWUP_DAYS:
                c = db.get(Consultant, s.consultant_id)
                j = db.get(Job, s.job_id)
                vendor = db.get(Vendor, s.vendor_id) if s.vendor_id else None
                message = get_llm().complete(
                    f"Write a polite day-{elapsed} follow-up to a vendor about {c.name} "
                    f"for the {j.title} role.",
                    system="FitLens Follow-up Agent",
                )
                action = {
                    "submission_id": s.id,
                    "day": elapsed,
                    "consultant": c.name,
                    "job": j.title,
                    "vendor": vendor.name if vendor else None,
                    "channel": "email",
                    "message": message,
                }
                if send and vendor and vendor.contact_email:
                    action["delivery"] = get_email_connector().send(
                        vendor.contact_email, f"Following up: {c.name} – {j.title}", message
                    )
                due.append(action)
        return {"due_followups": due, "count": len(due)}


# ───────────────────────── Agent 10: Interview Coordinator ─────────────────────────


class InterviewAgent(BaseAgent):
    name = "interview"
    description = "Proposes interview slots and manages confirmations/reminders."

    def _next_business_slots(self, start: date, n: int = 3) -> list[datetime]:
        slots, d = [], start
        while len(slots) < n:
            d += timedelta(days=1)
            if d.weekday() < 5:  # Mon-Fri
                slots.append(datetime.combine(d, time(15, 0), tzinfo=timezone.utc))
        return slots

    def schedule(self, db: Session, submission_id: int, today: date | None = None) -> dict:
        s = db.get(Submission, submission_id)
        if not s:
            raise ValueError("submission not found")
        slots = self._next_business_slots(today or date.today())
        interview = Interview(
            submission_id=s.id,
            scheduled_at=slots[0],
            mode="video",
            status="proposed",
            panel="Hiring Manager",
        )
        s.status = SubmissionStatus.INTERVIEW
        db.add_all([interview, s])
        db.commit()
        db.refresh(interview)
        confirmation = get_llm().complete(
            f"Write an interview confirmation for submission {s.id} proposing "
            f"{slots[0].isoformat()} (video).",
            system="FitLens Interview Coordinator",
        )
        return {
            "interview_id": interview.id,
            "submission_id": s.id,
            "proposed_slots": [sl.isoformat() for sl in slots],
            "scheduled_at": slots[0].isoformat(),
            "confirmation": confirmation,
        }

    def run(self, db: Session, submission_id: int, **kw) -> dict:
        return self.schedule(db, submission_id, **kw)
