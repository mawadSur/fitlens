"""Realistic seed data so the platform is demoable end-to-end out of the box."""
from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import SessionLocal, init_db
from .models import (
    Consultant,
    ConsultantStatus,
    ImmigrationRecord,
    Job,
    RateCard,
    Resume,
    Vendor,
    VisaStatus,
)

TODAY = date.today()


def _d(offset_days: int) -> date:
    return TODAY + timedelta(days=offset_days)


def _resume_text(name: str, skills: list[str], years: float, title: str) -> str:
    return (
        f"{name}\n{title} with {years:.0f}+ years of experience.\n"
        f"Core skills: {', '.join(skills)}.\n"
        f"Delivered production systems using {', '.join(skills[:4])}. "
        f"Strong background in {title.lower()} and cross-functional delivery."
    )


def seed(db: Session) -> dict:
    # ── Vendors ──
    vendors = [
        Vendor(name="Apex Staffing Partners", contact_email="reqs@apexstaffing.example", tier="A",
               response_rate=0.72, avg_response_hours=6, placements_count=18),
        Vendor(name="Vertex Talent Group", contact_email="hotlist@vertextalent.example", tier="B",
               response_rate=0.48, avg_response_hours=24, placements_count=7),
        Vendor(name="Beacon IT Vendors", contact_email="jobs@beaconit.example", tier="B",
               response_rate=0.35, avg_response_hours=40, placements_count=4),
        Vendor(name="Summit Prime", contact_email="bench@summitprime.example", tier="C",
               response_rate=0.20, avg_response_hours=72, placements_count=1),
    ]
    db.add_all(vendors)
    db.flush()

    # ── Rate cards ──
    db.add_all([
        RateCard(skill="databricks", min_rate=75, max_rate=110, demand_score=92),
        RateCard(skill="react", min_rate=55, max_rate=85, demand_score=80),
        RateCard(skill="java", min_rate=60, max_rate=95, demand_score=78),
        RateCard(skill="python", min_rate=60, max_rate=100, demand_score=88),
        RateCard(skill="aws", min_rate=65, max_rate=105, demand_score=85),
        RateCard(skill="salesforce", min_rate=60, max_rate=95, demand_score=70),
        RateCard(skill="qa automation", min_rate=50, max_rate=80, demand_score=62),
        RateCard(skill=".net", min_rate=58, max_rate=92, demand_score=66),
    ])

    # ── Consultants (name, visa, status, primary, skills, years, rate, bench_cost, avail, bench_start) ──
    spec = [
        ("Chandru Rao", VisaStatus.H1B, ConsultantStatus.ON_PROJECT, "Data Engineer",
         ["databricks", "spark", "python", "airflow", "sql", "aws", "etl"], 9, 95, 360, _d(21), None,
         dict(work_auth_end=_d(400), i94_expiry=_d(400), lca_filed=True, worksite="Dallas, TX")),
        ("Maria Gomez", VisaStatus.GC, ConsultantStatus.MARKETING, "Frontend Engineer",
         ["react", "typescript", "node.js", "next.js", "graphql", "javascript"], 7, 80, 320, None, _d(-50),
         dict(work_auth_end=None, lca_filed=False, worksite="Remote")),
        ("Wei Chen", VisaStatus.STEM_OPT, ConsultantStatus.MARKETING, "Backend Engineer",
         ["java", "spring boot", "microservices", "kafka", "postgresql", "rest"], 4, 72, 300, None, _d(-30),
         dict(ead_expiry=_d(75), i94_expiry=_d(120), lca_filed=False, worksite="Austin, TX")),
        ("Priya Patel", VisaStatus.OPT, ConsultantStatus.AVAILABLE, "ML Engineer",
         ["python", "machine learning", "pytorch", "nlp", "llm", "data science"], 3, 78, 310, _d(10), _d(-15),
         dict(ead_expiry=_d(200), i94_expiry=_d(300), lca_filed=False, worksite="Remote")),
        ("John Smith", VisaStatus.USC, ConsultantStatus.MARKETING, "DevOps Engineer",
         ["aws", "kubernetes", "docker", "terraform", "ci/cd", "linux", "jenkins"], 8, 100, 0, None, _d(-12),
         dict(work_auth_end=None, lca_filed=False, worksite="Remote")),
        ("Ahmed Khan", VisaStatus.H1B, ConsultantStatus.ON_PROJECT, ".NET Engineer",
         [".net", "c#", "azure", "sql", "microservices"], 10, 92, 350, _d(60), None,
         dict(work_auth_end=_d(500), i94_expiry=_d(500), lca_filed=True, worksite="Chicago, IL")),
        ("Sofia Rossi", VisaStatus.GC_EAD, ConsultantStatus.MARKETING, "Salesforce Developer",
         ["salesforce", "rest", "javascript", "agile"], 6, 85, 330, None, _d(-8),
         dict(ead_expiry=_d(40), lca_filed=False, worksite="Remote")),
        ("David Kim", VisaStatus.H4_EAD, ConsultantStatus.AVAILABLE, "QA Automation Engineer",
         ["qa automation", "selenium", "cypress", "playwright", "python", "ci/cd"], 5, 68, 290, _d(5), _d(-20),
         dict(ead_expiry=_d(110), i94_expiry=_d(220), lca_filed=False, worksite="Remote")),
    ]
    consultants = []
    for name, visa, status, title, skills, yrs, rate, bench_cost, avail, bench_start, imm in spec:
        c = Consultant(
            name=name, email=name.lower().replace(" ", ".") + "@consultants.example",
            phone="+1-555-0100", visa_status=visa, status=status, location=imm["worksite"],
            primary_skill=title, skills=skills, years_experience=yrs, expected_rate=rate,
            daily_bench_cost=bench_cost, availability_date=avail, bench_start_date=bench_start,
        )
        db.add(c)
        db.flush()
        db.add(Resume(consultant_id=c.id, filename=f"{name.replace(' ', '_')}_resume.txt",
                      content_text=_resume_text(name, skills, yrs, title),
                      parsed_skills=skills, is_primary=True))
        db.add(ImmigrationRecord(
            consultant_id=c.id, visa_type=visa, work_auth_start=_d(-365),
            work_auth_end=imm.get("work_auth_end"), ead_expiry=imm.get("ead_expiry"),
            i94_expiry=imm.get("i94_expiry"), lca_filed=imm.get("lca_filed", False),
            worksite_location=imm.get("worksite", ""),
        ))
        consultants.append(c)

    # ── Jobs (title, client, vendor_idx, location, remote, skills, min, max, visa_reqs, source) ──
    jobs_spec = [
        ("Senior Databricks Data Engineer", "FinServ Corp", 0, "Dallas, TX", True,
         ["databricks", "spark", "python", "aws", "etl"], 85, 110, ["H1B", "GC", "USC"], "jobdiva"),
        ("Lead React Developer", "RetailCo", 0, "Remote", True,
         ["react", "typescript", "next.js", "graphql"], 70, 95, [], "dice"),
        ("Java Microservices Engineer", "HealthTech", 1, "Austin, TX", False,
         ["java", "spring boot", "kafka", "microservices"], 65, 90, ["GC", "USC", "STEM_OPT"], "bullhorn"),
        ("Machine Learning Engineer (NLP)", "AI Labs", 1, "Remote", True,
         ["python", "machine learning", "nlp", "pytorch"], 80, 120, [], "linkedin"),
        ("Senior DevOps / Platform Engineer", "CloudOps Inc", 2, "Remote", True,
         ["aws", "kubernetes", "terraform", "ci/cd"], 90, 125, ["USC", "GC"], "ceipal"),
        (".NET Cloud Engineer", "InsureRight", 2, "Chicago, IL", False,
         [".net", "c#", "azure", "microservices"], 75, 100, ["H1B", "GC", "USC"], "jobdiva"),
        ("Salesforce Developer", "SalesForceOne", 3, "Remote", True,
         ["salesforce", "rest", "agile"], 65, 95, [], "indeed"),
        ("QA Automation Engineer", "QualityWorks", 0, "Remote", True,
         ["qa automation", "selenium", "playwright", "python"], 55, 82, [], "dice"),
    ]
    for title, client, vidx, loc, remote, skills, mn, mx, reqs, source in jobs_spec:
        db.add(Job(title=title, client=client, vendor_id=vendors[vidx].id, location=loc, remote=remote,
                   description=f"{title} for {client}. Requires {', '.join(skills)}.",
                   required_skills=skills, min_rate=mn, max_rate=mx, visa_requirements=reqs,
                   source=source, status="open"))

    db.commit()
    return {
        "consultants": len(consultants),
        "jobs": len(jobs_spec),
        "vendors": len(vendors),
    }


def reset_and_seed() -> dict:
    init_db()
    with SessionLocal() as db:
        if db.scalars(select(Consultant)).first():
            return {"skipped": "already seeded"}
        return seed(db)


def force_reseed() -> dict:
    from .db import Base, engine

    Base.metadata.drop_all(bind=engine)
    init_db()
    with SessionLocal() as db:
        return seed(db)


if __name__ == "__main__":
    print(reset_and_seed())
