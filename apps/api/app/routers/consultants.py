from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Consultant
from ..serializers import consultant_brief, consultant_detail

router = APIRouter(prefix="/api/consultants", tags=["consultants"])


@router.get("")
def list_consultants(db: Session = Depends(get_db)) -> list[dict]:
    return [consultant_brief(c) for c in db.scalars(select(Consultant)).all()]


@router.get("/{consultant_id}")
def get_consultant(consultant_id: int, db: Session = Depends(get_db)) -> dict:
    c = db.get(Consultant, consultant_id)
    if not c:
        raise HTTPException(404, "consultant not found")
    return consultant_detail(c)
