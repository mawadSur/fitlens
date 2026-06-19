from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Job, Vendor
from ..serializers import job_brief, vendor_brief

router = APIRouter(prefix="/api", tags=["jobs"])


@router.get("/jobs")
def list_jobs(db: Session = Depends(get_db)) -> list[dict]:
    return [job_brief(j) for j in db.scalars(select(Job)).all()]


@router.get("/jobs/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db)) -> dict:
    j = db.get(Job, job_id)
    if not j:
        raise HTTPException(404, "job not found")
    d = job_brief(j)
    d["description"] = j.description
    return d


@router.get("/vendors")
def list_vendors(db: Session = Depends(get_db)) -> list[dict]:
    return [vendor_brief(v) for v in db.scalars(select(Vendor)).all()]
