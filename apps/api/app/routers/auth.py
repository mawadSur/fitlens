"""Auth endpoints: dev token minting, principal introspection, role listing."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..auth import Principal, Role, create_access_token, get_current_principal
from ..config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


class TokenRequest(BaseModel):
    email: str
    role: Role = Role.VIEWER


@router.post("/token")
def issue_token(body: TokenRequest) -> dict:
    """Dev-only token mint. Disabled unless ``auth_provider == 'dev'``."""
    if settings.auth_provider != "dev":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="dev token endpoint is disabled",
        )
    token = create_access_token(sub=body.email, role=body.role)
    return {"access_token": token, "token_type": "bearer", "role": body.role.value}


@router.get("/me")
def me(principal: Principal = Depends(get_current_principal)) -> dict:
    return {"sub": principal.sub, "role": principal.role.value}


@router.get("/roles")
def roles() -> list[str]:
    return [r.value for r in Role]
