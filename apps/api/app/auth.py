"""RBAC scaffolding: roles, JWT tokens, and FastAPI auth dependencies.

Auth is NOT enforced by default (``settings.auth_enforced is False``). In that
mode a request without a token is treated as a dev ``admin`` principal so every
existing route keeps working unauthenticated. Set ``AUTH_ENFORCED=true`` to
require a valid bearer token.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings


class Role(str, enum.Enum):
    ADMIN = "admin"
    ACCOUNT_MANAGER = "account_manager"
    RECRUITER = "recruiter"
    BENCH_SALES = "bench_sales"
    VIEWER = "viewer"


@dataclass
class Principal:
    sub: str
    role: Role


def create_access_token(sub: str, role: Role, *, ttl_minutes: int | None = None) -> str:
    """Sign an HS256 access token with sub/role and an exp claim."""
    if ttl_minutes is None:
        ttl_minutes = settings.access_token_ttl_minutes
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "role": Role(role).value,
        "iat": now,
        "exp": now + timedelta(minutes=ttl_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    """Decode/verify a token. Raises ``jwt.PyJWTError`` on invalid/expired."""
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


# auto_error=False so we can fall back to the dev admin principal when unenforced.
_bearer = HTTPBearer(auto_error=False)


def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> Principal:
    """Resolve the caller. Token wins; otherwise dev-admin (unenforced) or 401."""
    if credentials is not None:
        try:
            claims = decode_token(credentials.credentials)
        except jwt.PyJWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc
        try:
            role = Role(claims.get("role", Role.VIEWER.value))
        except ValueError:
            role = Role.VIEWER
        return Principal(sub=str(claims.get("sub", "")), role=role)

    if not settings.auth_enforced:
        return Principal(sub="dev-admin", role=Role.ADMIN)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_role(*roles: Role):
    """Dependency factory: 403s unless the principal holds one of ``roles``.

    ADMIN is always allowed.
    """
    allowed = {Role(r) for r in roles}

    def _dependency(principal: Principal = Depends(get_current_principal)) -> Principal:
        if principal.role is Role.ADMIN or principal.role in allowed:
            return principal
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="insufficient role",
        )

    return _dependency
