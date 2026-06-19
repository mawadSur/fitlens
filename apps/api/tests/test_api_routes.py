"""Integration tests for all API routes — currently zero coverage."""
import pytest
from unittest.mock import patch


# ─── /api/consultants ─────────────────────────────────────────────────────────

def test_list_consultants_200(client):
    resp = client.get("/api/consultants")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_list_consultants_entry_schema(client):
    resp = client.get("/api/consultants")
    c = resp.json()[0]
    for key in ("id", "name", "email", "visa_status", "status", "primary_skill"):
        assert key in c


def test_get_consultant_200(client):
    all_cs = client.get("/api/consultants").json()
    cid = all_cs[0]["id"]
    resp = client.get(f"/api/consultants/{cid}")
    assert resp.status_code == 200
    assert resp.json()["id"] == cid


def test_get_consultant_404(client):
    resp = client.get("/api/consultants/999999")
    assert resp.status_code == 404


def test_get_consultant_detail_has_resumes(client):
    all_cs = client.get("/api/consultants").json()
    cid = all_cs[0]["id"]
    resp = client.get(f"/api/consultants/{cid}")
    assert "resumes" in resp.json()


# ─── /api/jobs ────────────────────────────────────────────────────────────────

def test_list_jobs_200(client):
    resp = client.get("/api/jobs")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_get_job_200(client):
    jobs = client.get("/api/jobs").json()
    jid = jobs[0]["id"]
    resp = client.get(f"/api/jobs/{jid}")
    assert resp.status_code == 200
    assert "description" in resp.json()


def test_get_job_404(client):
    resp = client.get("/api/jobs/999999")
    assert resp.status_code == 404


# ─── /api/vendors ─────────────────────────────────────────────────────────────

def test_list_vendors_200(client):
    resp = client.get("/api/vendors")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


# ─── /api/dashboard ───────────────────────────────────────────────────────────

def test_dashboard_200(client):
    resp = client.get("/api/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    for key in ("counts", "hot_bench", "bench_alerts", "immigration_alerts",
                "revenue_forecast", "top_placements"):
        assert key in data


def test_dashboard_counts_schema(client):
    resp = client.get("/api/dashboard")
    counts = resp.json()["counts"]
    for key in ("consultants", "open_jobs", "submissions", "placements", "interviews"):
        assert key in counts


# ─── /api/agents ──────────────────────────────────────────────────────────────

def test_list_agents_200(client):
    resp = client.get("/api/agents")
    assert resp.status_code == 200
    assert "agents" in resp.json()
    assert resp.json()["count"] > 0


def test_run_agent_bench_200(client):
    resp = client.post("/api/agents/bench/run", json={})
    assert resp.status_code == 200
    assert "result" in resp.json()


def test_run_agent_unknown_404(client):
    resp = client.post("/api/agents/nonexistent_agent/run", json={})
    assert resp.status_code == 404


def test_run_agent_matching_invalid_id_400(client):
    resp = client.post("/api/agents/matching/run", json={"consultant_id": 999999})
    assert resp.status_code == 400


# ─── /api/market ──────────────────────────────────────────────────────────────

def test_market_all_200(client):
    resp = client.get("/api/market")
    assert resp.status_code == 200
    assert "top_skills" in resp.json()


def test_market_with_skill_200(client):
    resp = client.get("/api/market?skill=python")
    assert resp.status_code == 200
    data = resp.json()
    assert data["skill"].lower() == "python"


# ─── /api/immigration ─────────────────────────────────────────────────────────

def test_immigration_200(client):
    resp = client.get("/api/immigration")
    assert resp.status_code == 200
    assert "alerts" in resp.json()


# ─── /api/placement ───────────────────────────────────────────────────────────

def test_placement_200(client):
    resp = client.get("/api/placement")
    assert resp.status_code == 200
    assert "predictions" in resp.json()


# ─── /api/revenue ─────────────────────────────────────────────────────────────

def test_revenue_200(client):
    resp = client.get("/api/revenue")
    assert resp.status_code == 200
    assert "expected_monthly_revenue" in resp.json()


# ─── /api/integrations ────────────────────────────────────────────────────────

def test_integrations_200(client):
    resp = client.get("/api/integrations")
    assert resp.status_code == 200
    assert "connectors" in resp.json()
    assert "embedder_backend" in resp.json()


# ─── Workflow routes ──────────────────────────────────────────────────────────

def test_consultant_matches_200(client):
    cs = client.get("/api/consultants").json()
    cid = cs[0]["id"]
    resp = client.get(f"/api/consultants/{cid}/matches?top_k=3")
    assert resp.status_code == 200
    assert "matches" in resp.json()


def test_consultant_matches_404_unknown(client):
    resp = client.get("/api/consultants/999999/matches")
    assert resp.status_code == 404


def test_job_candidates_200(client):
    jobs = client.get("/api/jobs").json()
    jid = jobs[0]["id"]
    resp = client.get(f"/api/jobs/{jid}/candidates?top_k=3")
    assert resp.status_code == 200
    assert "candidates" in resp.json()


def test_job_candidates_404_unknown(client):
    resp = client.get("/api/jobs/999999/candidates")
    assert resp.status_code == 404


def test_list_submissions_200(client):
    resp = client.get("/api/submissions")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_create_submission_200(client):
    cs = client.get("/api/consultants").json()
    jobs = client.get("/api/jobs").json()
    payload = {"consultant_id": cs[0]["id"], "job_id": jobs[0]["id"]}
    resp = client.post("/api/submissions", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["consultant_id"] == cs[0]["id"]
    assert data["status"] == "submitted"


def test_create_submission_400_invalid_consultant(client):
    jobs = client.get("/api/jobs").json()
    payload = {"consultant_id": 999999, "job_id": jobs[0]["id"]}
    resp = client.post("/api/submissions", json=payload)
    assert resp.status_code == 400


def test_schedule_interview_200(client):
    cs = client.get("/api/consultants").json()
    jobs = client.get("/api/jobs").json()
    sub = client.post(
        "/api/submissions",
        json={"consultant_id": cs[0]["id"], "job_id": jobs[0]["id"]},
    ).json()
    with patch("app.agents.outreach.get_llm") as mock_llm:
        mock_llm.return_value.complete.return_value = "Interview confirmed."
        resp = client.post(f"/api/submissions/{sub['submission_id']}/interview")
    assert resp.status_code == 200
    assert "interview_id" in resp.json()


def test_schedule_interview_404_unknown(client):
    resp = client.post("/api/submissions/999999/interview")
    assert resp.status_code == 404


def test_followups_200(client):
    resp = client.get("/api/followups")
    assert resp.status_code == 200
    assert "due_followups" in resp.json()


# ─── Resume upload ────────────────────────────────────────────────────────────

def test_upload_resume_200(client):
    cs = client.get("/api/consultants").json()
    cid = cs[0]["id"]
    content = b"Experienced Python developer with AWS and Kubernetes experience."
    resp = client.post(
        f"/api/consultants/{cid}/resume",
        files={"file": ("resume.txt", content, "text/plain")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "resume_id" in data
    assert "parsed_skills" in data
    assert "python" in data["parsed_skills"]


def test_upload_resume_404_unknown_consultant(client):
    content = b"Some resume content."
    resp = client.post(
        "/api/consultants/999999/resume",
        files={"file": ("resume.txt", content, "text/plain")},
    )
    assert resp.status_code == 404
