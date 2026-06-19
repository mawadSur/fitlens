"""Analytics agents: Placement Prediction, Revenue Forecast."""
from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import scoring
from ..models import Consultant, ConsultantStatus, Interview, Submission, SubmissionStatus
from .base import BaseAgent, days_on_bench
from .matching import MatchingAgent

HOURS_PER_MONTH = 160
DEFAULT_GROSS_MARGIN = 0.22


def _active_interviews(db: Session, consultant_id: int) -> int:
    rows = db.execute(
        select(Interview)
        .join(Submission, Interview.submission_id == Submission.id)
        .where(Submission.consultant_id == consultant_id)
        .where(Interview.status.in_(["proposed", "scheduled", "confirmed"]))
    ).all()
    return len(rows)


def _marketed(db: Session) -> list[Consultant]:
    return db.scalars(
        select(Consultant).where(
            Consultant.status.in_([ConsultantStatus.AVAILABLE, ConsultantStatus.MARKETING])
        )
    ).all()


# ───────────────────────── Agent 11: Placement Prediction ─────────────────────────


class PlacementAgent(BaseAgent):
    name = "placement"
    description = "Predicts probability of placement per consultant."

    def predict(self, db: Session, consultant: Consultant) -> dict:
        matcher = MatchingAgent()
        result = matcher.match_consultant(db, consultant.id, top_k=1)
        best = result["matches"][0] if result["matches"] else None
        match_score = best["match_score"] if best else 0.0
        vendor_score = best["vendor_score"] if best else 50.0
        interviews = _active_interviews(db, consultant.id)
        dob = days_on_bench(consultant.bench_start_date)
        prob = scoring.placement_probability(match_score, vendor_score, 60.0, interviews, dob)
        return {
            "consultant_id": consultant.id,
            "name": consultant.name,
            "best_match_score": match_score,
            "best_job": best["title"] if best else None,
            "active_interviews": interviews,
            "days_on_bench": dob,
            "placement_probability": prob,
            "forecast": f"{int(prob * 100)}% probability of placement within 14 days.",
        }

    def run(self, db: Session, consultant_id: int | None = None) -> dict:
        if consultant_id:
            c = db.get(Consultant, consultant_id)
            if not c:
                raise ValueError("consultant not found")
            return self.predict(db, c)
        preds = sorted(
            (self.predict(db, c) for c in _marketed(db)),
            key=lambda d: d["placement_probability"],
            reverse=True,
        )
        return {"predictions": preds, "count": len(preds)}


# ───────────────────────── Agent 12: Revenue Forecast ─────────────────────────


class RevenueAgent(BaseAgent):
    name = "revenue"
    description = "Forecasts placements, revenue, margin, and bench burn."

    def run(self, db: Session, gross_margin: float = DEFAULT_GROSS_MARGIN, today: date | None = None) -> dict:
        placement = PlacementAgent()
        marketed = _marketed(db)
        expected_placements = 0.0
        expected_monthly_revenue = 0.0
        weighted_margin = 0.0
        for c in marketed:
            pred = placement.predict(db, c)
            p = pred["placement_probability"]
            expected_placements += p
            monthly_rev = c.expected_rate * HOURS_PER_MONTH
            expected_monthly_revenue += p * monthly_rev
            weighted_margin += p * monthly_rev * gross_margin

        benched = [
            c for c in marketed if c.status in (ConsultantStatus.AVAILABLE, ConsultantStatus.MARKETING)
        ]
        daily_burn = sum(c.daily_bench_cost for c in benched)

        placed = db.scalars(
            select(Submission).where(Submission.status == SubmissionStatus.PLACED)
        ).all()

        return {
            "expected_placements_30d": round(expected_placements, 2),
            "expected_monthly_revenue": round(expected_monthly_revenue, 2),
            "expected_gross_margin": round(weighted_margin, 2),
            "gross_margin_pct": gross_margin,
            "bench_burn_daily": round(daily_burn, 2),
            "bench_burn_monthly": round(daily_burn * 30, 2),
            "consultants_marketed": len(marketed),
            "placements_to_date": len(placed),
        }
