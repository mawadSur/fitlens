"""Matching-side agents: Market Intelligence, Job Matching, Vendor Relationship."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import scoring
from ..embeddings import cosine_similarity, embed_text, get_vector_store
from ..models import Consultant, Job, RateCard, Vendor
from .base import BaseAgent, days_on_bench

# ───────────────────────── Agent 6: Vendor Relationship ─────────────────────────


def score_vendor(v: Vendor) -> float:
    """Composite 0..100 vendor quality score."""
    tier_bonus = {"A": 20, "B": 10, "C": 0}.get(v.tier, 0)
    responsiveness = max(0.0, 1.0 - min(v.avg_response_hours, 96) / 96) * 30
    rate = (v.response_rate or 0) * 30
    placements = min(v.placements_count, 20) / 20 * 20
    return round(min(100.0, tier_bonus + responsiveness + rate + placements), 1)


class VendorAgent(BaseAgent):
    name = "vendor"
    description = "Scores and ranks vendors by responsiveness and placement history."

    def run(self, db: Session, top_k: int = 10) -> dict:
        vendors = db.scalars(select(Vendor)).all()
        ranked = sorted(
            (
                {
                    "vendor_id": v.id,
                    "name": v.name,
                    "tier": v.tier,
                    "score": score_vendor(v),
                    "response_rate": v.response_rate,
                    "avg_response_hours": v.avg_response_hours,
                    "placements": v.placements_count,
                }
                for v in vendors
            ),
            key=lambda d: d["score"],
            reverse=True,
        )
        return {"top_vendors": ranked[:top_k], "count": len(ranked)}


# ───────────────────────── Agent 4: Market Intelligence ─────────────────────────


class MarketAgent(BaseAgent):
    name = "market"
    description = "Estimates skill demand and recommended bill rates."

    def demand_for(self, db: Session, skill: str) -> dict:
        s = skill.lower()
        card = db.scalars(
            select(RateCard).where(func.lower(RateCard.skill) == s)
        ).first()
        job_count = sum(
            1
            for j in db.scalars(select(Job).where(Job.status == "open")).all()
            if s in [x.lower() for x in j.required_skills]
        )
        demand = card.demand_score if card else min(100.0, 40 + job_count * 8)
        return {
            "skill": skill,
            "demand_score": round(demand, 1),
            "open_jobs": job_count,
            "recommended_rate": {
                "min": card.min_rate if card else 55.0,
                "max": card.max_rate if card else 90.0,
            },
        }

    def run(self, db: Session, skill: str | None = None) -> dict:
        if skill:
            return self.demand_for(db, skill)
        cards = db.scalars(select(RateCard).order_by(RateCard.demand_score.desc())).all()
        return {
            "top_skills": [
                {"skill": c.skill, "demand_score": c.demand_score, "rate": [c.min_rate, c.max_rate]}
                for c in cards[:10]
            ]
        }


# ───────────────────────── Agent 5: Job Matching ─────────────────────────


class MatchingAgent(BaseAgent):
    name = "matching"
    description = "Matches consultants to jobs via embeddings + scoring engine."

    def _consultant_vector(self, db: Session, c: Consultant) -> list[float]:
        # Represent the consultant by their PRIMARY (marketed) resume — never by
        # whichever resume happens to have a cached embedding.
        primary = next((r for r in c.resumes if r.is_primary), None)
        if primary and primary.embedding:
            return primary.embedding
        if primary and primary.content_text:
            return embed_text(primary.content_text)
        return embed_text(f"{c.primary_skill} {' '.join(c.skills)}")

    def _job_vector(self, db: Session, j: Job) -> list[float]:
        if j.embedding:
            return j.embedding
        vec = embed_text(f"{j.title} {j.description} {' '.join(j.required_skills)}")
        j.embedding = vec
        db.add(j)
        db.commit()
        return vec

    def _breakdown(self, c: Consultant, j: Job, semantic: float) -> dict:
        skill = scoring.skill_overlap(c.skills, j.required_skills)
        rate = scoring.rate_fit(c.expected_rate, j.min_rate, j.max_rate)
        visa_ok = scoring.visa_allows(c.visa_status.value, j.visa_requirements)
        match = scoring.composite_match(semantic, skill, rate, visa_ok)
        vscore = score_vendor(j.vendor) if j.vendor else 50.0
        return {
            "match_score": match,
            "semantic": round(semantic, 3),
            "skill_overlap": round(skill, 3),
            "rate_fit": round(rate, 3),
            "visa_eligible": visa_ok,
            "vendor_score": vscore,
            "interview_probability": scoring.interview_probability(match, vscore),
        }

    def match_consultant(self, db: Session, consultant_id: int, top_k: int = 5) -> dict:
        c = db.get(Consultant, consultant_id)
        if not c:
            raise ValueError("consultant not found")
        cvec = self._consultant_vector(db, c)
        jobs = db.scalars(select(Job).where(Job.status == "open")).all()
        candidates = [(j.id, self._job_vector(db, j)) for j in jobs]
        ranked = get_vector_store().rank(cvec, candidates)
        jobs_by_id = {j.id: j for j in jobs}
        dob = days_on_bench(c.bench_start_date)
        out = []
        for item in ranked:
            j = jobs_by_id[item.id]
            bd = self._breakdown(c, j, item.score)
            pp = scoring.placement_probability(
                bd["match_score"], bd["vendor_score"], 60.0, 0, dob
            )
            out.append(
                {
                    "job_id": j.id,
                    "title": j.title,
                    "client": j.client,
                    "location": j.location,
                    "rate_band": [j.min_rate, j.max_rate],
                    "source": j.source,
                    "placement_probability": pp,
                    **bd,
                }
            )
        # Rank by the composite match score shown in the UI (robust to resume noise).
        out.sort(key=lambda m: m["match_score"], reverse=True)
        return {"consultant_id": c.id, "matches": out[:top_k]}

    def match_job(self, db: Session, job_id: int, top_k: int = 5) -> dict:
        j = db.get(Job, job_id)
        if not j:
            raise ValueError("job not found")
        jvec = self._job_vector(db, j)
        consultants = db.scalars(select(Consultant)).all()
        scored = []
        for c in consultants:
            semantic = cosine_similarity(jvec, self._consultant_vector(db, c))
            bd = self._breakdown(c, j, semantic)
            scored.append(
                {
                    "consultant_id": c.id,
                    "name": c.name,
                    "visa_status": c.visa_status.value,
                    "primary_skill": c.primary_skill,
                    **bd,
                }
            )
        scored.sort(key=lambda d: d["match_score"], reverse=True)
        return {"job_id": j.id, "title": j.title, "candidates": scored[:top_k]}

    def run(self, db: Session, consultant_id: int, top_k: int = 5) -> dict:
        return self.match_consultant(db, consultant_id, top_k)
