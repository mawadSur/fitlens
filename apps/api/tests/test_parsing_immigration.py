"""Unit tests for resume parsing and the Immigration agent."""
from app.agents import ImmigrationAgent
from app.models import Consultant, VisaStatus
from app.parsing import extract_skills, extract_text


def test_extract_skills_finds_taxonomy_terms():
    text = "Built data pipelines with Python, Spark and Databricks on AWS. Some React too."
    skills = extract_skills(text)
    assert "python" in skills and "databricks" in skills and "aws" in skills and "react" in skills
    assert len(skills) == len(set(skills))  # de-duped


def test_extract_text_plaintext_fallback():
    assert "hello resume" in extract_text("cv.txt", b"hello resume")


def test_immigration_alerts_and_transfer_rules(db):
    out = ImmigrationAgent().run(db)
    joined = " ".join(out["alerts"])
    # Wei Chen (STEM OPT, EAD +75d) and Sofia (GC_EAD, +40d) are within the 90-day horizon
    assert "Wei Chen" in joined
    assert any(s["visa_type"] == "STEM_OPT" and s["transfer_eligible"] is False
               for s in out["authorizations"])
    assert any(s["visa_type"] == "H1B" and s["transfer_eligible"] is True
               for s in out["authorizations"])


def test_immigration_eligibility_helper(db):
    h1b = db.query(Consultant).filter_by(visa_status=VisaStatus.H1B).first()
    agent = ImmigrationAgent()
    assert agent.eligibility(h1b, ["H1B", "GC"])["eligible"] is True
    assert agent.eligibility(h1b, ["USC"])["eligible"] is False
