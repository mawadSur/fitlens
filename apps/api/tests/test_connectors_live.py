"""Credential-gated connector tests.

These exercise REAL connector code paths offline:
- mock fallback when creds are absent (no `_fetch_live` call),
- `status().missing_credentials` reporting,
- `_normalize()` parsing against representative raw upstream payloads,
- one full end-to-end LIVE run (Bullhorn) driven by a fake httpx transport.

No network is touched. Live `_fetch_live` bodies that build HTTP clients are
`# pragma: no cover` in source; we only execute Bullhorn's end-to-end via a
mocked transport, and the rest via direct `_normalize` calls.
"""
from __future__ import annotations

import httpx
import pytest

from app.config import settings
from app.connectors import jobsources
from app.connectors.comms import TeamsConnector
from app.connectors.jobsources import (
    BullhornConnector,
    CeipalConnector,
    DiceConnector,
    IndeedConnector,
    JobDivaConnector,
    LinkedInConnector,
    MonsterConnector,
)

# (connector class, list of its required_env keys) for the parametrized
# "no creds => mock" and "status reports missing" checks.
JOB_CONNECTORS = [
    (JobDivaConnector, JobDivaConnector.required_env),
    (BullhornConnector, BullhornConnector.required_env),
    (CeipalConnector, CeipalConnector.required_env),
    (DiceConnector, DiceConnector.required_env),
    (IndeedConnector, IndeedConnector.required_env),
    (MonsterConnector, MonsterConnector.required_env),
    (LinkedInConnector, LinkedInConnector.required_env),
]


@pytest.fixture
def no_creds(monkeypatch):
    """Force every connector credential to empty so all run in mock mode."""
    keys = {k for _, env in JOB_CONNECTORS for k in env}
    keys |= set(TeamsConnector.required_env)
    for k in keys:
        monkeypatch.setattr(settings, k, "", raising=False)
    return settings


# --------------------------------------------------------------------------- #
# Gating: no creds => not live, status lists missing keys, fetch returns mock  #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("cls,env", JOB_CONNECTORS, ids=[c.name for c, _ in JOB_CONNECTORS])
def test_not_live_without_creds(no_creds, cls, env):
    conn = cls()
    assert conn.is_live is False
    st = conn.status()
    assert st.live is False
    assert set(st.missing_credentials) == set(env)


@pytest.mark.parametrize("cls,env", JOB_CONNECTORS, ids=[c.name for c, _ in JOB_CONNECTORS])
def test_fetch_returns_mock_without_creds(no_creds, cls, env):
    conn = cls()
    rows = conn.fetch_jobs(query="python", limit=5)
    assert rows, "mock fetch must return at least one row"
    assert all(r.get("_mock") is True for r in rows)
    assert all(r["source"] == cls.name for r in rows)


# --------------------------------------------------------------------------- #
# Real parsing logic: feed each connector a representative raw upstream dict   #
# --------------------------------------------------------------------------- #


def test_normalize_jobdiva():
    raw = {
        "id": 555,
        "title": "Senior Python Engineer",
        "customerName": "Acme Corp",
        "city": "Austin, TX",
        "description": "Build APIs.",
        "skills": ["python", "fastapi"],
        "payRateFrom": "65",
        "payRateTo": "95",
    }
    out = JobDivaConnector()._normalize(raw)
    assert out["title"] == "Senior Python Engineer"
    assert out["client"] == "Acme Corp"
    assert out["min_rate"] == 65.0
    assert out["max_rate"] == 95.0
    assert out["source"] == "jobdiva"
    assert out["external_id"] == "555"


def test_normalize_bullhorn():
    raw = {
        "id": 42,
        "title": "Backend Engineer",
        "clientCorporation": {"name": "Globex"},
        "address": {"city": "Denver", "state": "CO"},
        "publicDescription": "Go and Python.",
        "skills": {"data": [{"name": "python"}, {"name": "go"}]},
        "payRate": 70,
        "salary": 110,
    }
    out = BullhornConnector()._normalize(raw)
    assert out["title"] == "Backend Engineer"
    assert out["client"] == "Globex"
    assert out["location"] == "Denver, CO"
    assert out["required_skills"] == ["python", "go"]
    assert out["min_rate"] == 70.0
    assert out["max_rate"] == 110.0
    assert out["source"] == "bullhorn"
    assert out["external_id"] == "42"


def test_normalize_ceipal():
    raw = {
        "id": "JOB-9",
        "position_title": "Data Engineer",
        "client": "Initech",
        "city": "Remote",
        "state": "US",
        "public_job_desc": "ETL pipelines.",
        "skills": "python, spark, airflow",
        "pay_rate_from": "60",
        "pay_rate_to": "85",
        "tax_terms": "W2, C2C",
    }
    out = CeipalConnector()._normalize(raw)
    assert out["title"] == "Data Engineer"
    assert out["client"] == "Initech"
    assert out["location"] == "Remote, US"
    assert out["required_skills"] == ["python", "spark", "airflow"]
    assert out["min_rate"] == 60.0
    assert out["max_rate"] == 85.0
    assert out["visa_requirements"] == ["W2", "C2C"]
    assert out["external_id"] == "JOB-9"


def test_normalize_dice():
    raw = {
        "id": "d-100",
        "title": "DevOps Engineer",
        "company": "Hooli",
        "location": "Seattle, WA",
        "summary": "Kubernetes and Terraform.",
        "skills": ["kubernetes", "terraform"],
        "compensation": {"min": 80, "max": 120},
    }
    out = DiceConnector()._normalize(raw)
    assert out["title"] == "DevOps Engineer"
    assert out["client"] == "Hooli"
    assert out["location"] == "Seattle, WA"
    assert out["required_skills"] == ["kubernetes", "terraform"]
    assert out["min_rate"] == 80.0
    assert out["max_rate"] == 120.0
    assert out["external_id"] == "d-100"


def test_normalize_indeed():
    raw = {
        "jobkey": "abc123",
        "jobtitle": "Software Engineer",
        "company": "Pied Piper",
        "formattedLocation": "Palo Alto, CA",
        "snippet": "Compression algorithms.",
    }
    out = IndeedConnector()._normalize(raw)
    assert out["title"] == "Software Engineer"
    assert out["client"] == "Pied Piper"
    assert out["location"] == "Palo Alto, CA"
    assert out["description"] == "Compression algorithms."
    assert out["source"] == "indeed"
    assert out["external_id"] == "abc123"


def test_normalize_monster():
    raw = {
        "jobId": "m-7",
        "title": "Full Stack Developer",
        "companyName": "Umbrella",
        "location": {"displayName": "Boston, MA"},
        "description": "React + Node.",
        "skills": ["react", "node"],
        "salary": {"min": 50, "max": 90},
    }
    out = MonsterConnector()._normalize(raw)
    assert out["title"] == "Full Stack Developer"
    assert out["client"] == "Umbrella"
    assert out["location"] == "Boston, MA"
    assert out["required_skills"] == ["react", "node"]
    assert out["min_rate"] == 50.0
    assert out["max_rate"] == 90.0
    assert out["external_id"] == "m-7"


def test_normalize_linkedin():
    raw = {
        "entityUrn": "urn:li:job:998",
        "title": "ML Engineer",
        "companyDetails": {"name": "Stark Industries"},
        "formattedLocation": "NYC, NY",
        "description": {"text": "Training models."},
        "skills": ["pytorch", "ml"],
    }
    out = LinkedInConnector()._normalize(raw)
    assert out["title"] == "ML Engineer"
    assert out["client"] == "Stark Industries"
    assert out["location"] == "NYC, NY"
    assert out["description"] == "Training models."
    assert out["required_skills"] == ["pytorch", "ml"]
    assert out["source"] == "linkedin"
    assert out["external_id"] == "urn:li:job:998"


# --------------------------------------------------------------------------- #
# End-to-end LIVE path for Bullhorn against a fake httpx transport (no net).   #
# --------------------------------------------------------------------------- #


def _bullhorn_transport() -> httpx.MockTransport:
    """Mimic Bullhorn's authorize -> token -> login -> search dance."""

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "oauth/authorize" in url:
            # Redirect to a callback carrying the auth code; httpx follows it.
            return httpx.Response(
                302, headers={"location": "https://app.example.com/cb?code=AUTHCODE"}
            )
        if "app.example.com/cb" in url:
            return httpx.Response(200, text="landed")
        if "oauth/token" in url:
            return httpx.Response(200, json={"access_token": "ACCESS"})
        if "rest-services/login" in url:
            return httpx.Response(
                200,
                json={
                    "restUrl": "https://rest99.bullhornstaffing.com/rest-services/abc/",
                    "BhRestToken": "BHTOKEN",
                },
            )
        if "search/JobOrder" in url:
            return httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "id": 1,
                            "title": "Live Engineer",
                            "clientCorporation": {"name": "LiveCo"},
                            "address": {"city": "Reno", "state": "NV"},
                            "publicDescription": "Real listing.",
                            "skills": {"data": [{"name": "python"}]},
                            "payRate": 75,
                            "salary": 130,
                        }
                    ]
                },
            )
        return httpx.Response(404, text=f"unexpected: {url}")

    return httpx.MockTransport(handler)


class _PatchedHttpx:
    """Shim exposing the same surface jobsources.py uses from `httpx`, but with
    `Client` pre-wired to our MockTransport so the real `_fetch_live` runs."""

    Response = httpx.Response
    Request = httpx.Request

    @staticmethod
    def Client(*args, **kwargs):  # noqa: N802 - mirror httpx.Client
        kwargs.pop("base_url", None)
        kwargs["transport"] = _bullhorn_transport()
        return httpx.Client(*args, **kwargs)


def test_bullhorn_live_end_to_end(monkeypatch):
    # 1. Make Bullhorn appear live by populating its creds on the shared settings.
    for k in BullhornConnector.required_env:
        monkeypatch.setattr(settings, k, "filled", raising=False)
    # 2. Swap the module's httpx so live HTTP calls hit the fake transport.
    monkeypatch.setattr(jobsources, "httpx", _PatchedHttpx)

    conn = BullhornConnector()
    assert conn.is_live is True

    rows = conn.fetch_jobs(query="engineer", limit=10)  # routes to _fetch_live
    assert len(rows) == 1
    row = rows[0]
    assert row["title"] == "Live Engineer"
    assert row["client"] == "LiveCo"
    assert row["location"] == "Reno, NV"
    assert row["required_skills"] == ["python"]
    assert row["min_rate"] == 75.0
    assert row["max_rate"] == 130.0
    assert row["source"] == "bullhorn"
    assert row["external_id"] == "1"
    assert "_mock" not in row


# --------------------------------------------------------------------------- #
# Teams comms: mock mode without creds.                                       #
# --------------------------------------------------------------------------- #


def test_teams_mock_without_creds(no_creds):
    conn = TeamsConnector()
    assert conn.is_live is False
    st = conn.status()
    assert set(st.missing_credentials) == set(TeamsConnector.required_env)
    result = conn.send(to="chat-1", subject="Hi", body="Hello there")
    assert result == {"sent": False, "mode": "mock", "to": "chat-1", "subject": "Hi"}
