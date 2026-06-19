"""Integration tests for the FastAPI endpoints via TestClient."""


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_list_consultants(client):
    r = client.get("/api/consultants")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 8
    assert {"name", "visa_status", "days_on_bench"} <= set(data[0])


def test_dashboard_shape(client):
    r = client.get("/api/dashboard")
    assert r.status_code == 200
    d = r.json()
    assert d["counts"]["consultants"] == 8
    assert "revenue_forecast" in d and "hot_bench" in d
    assert d["total_daily_bench_cost"] > 0


def test_consultant_matches_endpoint(client):
    r = client.get("/api/consultants/1/matches?top_k=3")
    assert r.status_code == 200
    matches = r.json()["matches"]
    assert matches and matches[0]["match_score"] > 0


def test_submission_then_interview_flow(client):
    # Create a submission for consultant 1 -> Databricks job (id 1)
    r = client.post("/api/submissions", json={"consultant_id": 1, "job_id": 1})
    assert r.status_code == 200, r.text
    sub = r.json()
    assert sub["status"] == "submitted" and "rtr" in sub
    sub_id = sub["submission_id"]

    # It appears in the submissions list
    listing = client.get("/api/submissions").json()
    assert any(s["id"] == sub_id for s in listing)

    # Schedule an interview against it
    iv = client.post(f"/api/submissions/{sub_id}/interview")
    assert iv.status_code == 200, iv.text
    assert iv.json()["proposed_slots"]


def test_integrations_status(client):
    r = client.get("/api/integrations")
    assert r.status_code == 200
    d = r.json()
    assert d["total"] >= 8
    # All connectors are mock by default (no creds in test env)
    assert d["live_count"] == 0
    assert any(c["name"] == "jobdiva" for c in d["connectors"])


def test_run_agent_endpoint(client):
    r = client.post("/api/agents/bench/run", json={"horizon_days": 30})
    assert r.status_code == 200
    assert r.json()["result"]["count"] >= 1
    assert client.post("/api/agents/nope/run").status_code == 404
