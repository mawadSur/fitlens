"""Unit tests for the Matching agent (embeddings + scoring integration)."""
from app.agents import MatchingAgent
from app.models import Consultant


def _by_name(db, name):
    return db.query(Consultant).filter(Consultant.name == name).first()


def test_databricks_consultant_top_match_is_databricks_job(db):
    chandru = _by_name(db, "Chandru Rao")
    result = MatchingAgent().match_consultant(db, chandru.id, top_k=3)
    top = result["matches"][0]
    assert "Databricks" in top["title"]
    assert top["match_score"] > 80
    assert top["visa_eligible"] is True
    assert top["skill_overlap"] >= 0.8


def test_visa_ineligible_job_is_penalised(db):
    # Chandru is H1B; the DevOps role requires USC/GC -> heavy penalty.
    chandru = _by_name(db, "Chandru Rao")
    result = MatchingAgent().match_consultant(db, chandru.id, top_k=8)
    devops = [m for m in result["matches"] if "DevOps" in m["title"]]
    assert devops and devops[0]["visa_eligible"] is False
    assert devops[0]["match_score"] < 40


def test_match_job_ranks_candidates(db):
    from app.models import Job

    job = db.query(Job).filter(Job.title.like("%Databricks%")).first()
    result = MatchingAgent().match_job(db, job.id, top_k=5)
    assert result["candidates"][0]["name"] == "Chandru Rao"
    scores = [c["match_score"] for c in result["candidates"]]
    assert scores == sorted(scores, reverse=True)
