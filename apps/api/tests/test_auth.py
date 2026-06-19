"""Tests for RBAC scaffolding: token roundtrip, /api/auth endpoints, require_role."""
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.auth import Principal, Role, create_access_token, decode_token, require_role


def test_token_roundtrip_preserves_role():
    token = create_access_token("alice@example.com", Role.RECRUITER)
    claims = decode_token(token)
    assert claims["sub"] == "alice@example.com"
    assert claims["role"] == Role.RECRUITER.value
    assert "exp" in claims


def test_post_token_returns_bearer(client):
    r = client.post("/api/auth/token", json={"email": "bob@example.com", "role": "recruiter"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["role"] == "recruiter"
    assert body["access_token"]


def test_me_returns_principal_for_token(client):
    token = client.post(
        "/api/auth/token", json={"email": "carol@example.com", "role": "account_manager"}
    ).json()["access_token"]
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["sub"] == "carol@example.com"
    assert body["role"] == "account_manager"


def test_roles_lists_five(client):
    r = client.get("/api/auth/roles")
    assert r.status_code == 200
    roles = r.json()
    assert len(roles) == 5
    assert set(roles) == {
        "admin",
        "account_manager",
        "recruiter",
        "bench_sales",
        "viewer",
    }


def _admin_only_app() -> TestClient:
    app = FastAPI()

    @app.get("/admin-only")
    def admin_only(principal: Principal = Depends(require_role(Role.ADMIN))) -> dict:
        return {"sub": principal.sub, "role": principal.role.value}

    return TestClient(app)


def test_require_role_denies_viewer():
    tc = _admin_only_app()
    token = create_access_token("viewer@example.com", Role.VIEWER)
    r = tc.get("/admin-only", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


def test_require_role_allows_admin():
    tc = _admin_only_app()
    token = create_access_token("admin@example.com", Role.ADMIN)
    r = tc.get("/admin-only", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["role"] == "admin"
