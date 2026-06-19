"""Resume upload, matching, submissions, interviews — the core recruiter workflow."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..agents import (
    FollowupAgent,
    InterviewAgent,
    MatchingAgent,
    ResumeAgent,
    SubmissionAgent,
)
from ..db import get_db
from ..models import Consultant, Resume, Submission
from ..parsing import extract_skills, extract_text
from ..serializers import interview_brief, submission_brief

router = APIRouter(prefix="/api", tags=["workflow"])


# ── Resume upload + parse ──
@router.post("/consultants/{consultant_id}/resume")
async def upload_resume(
    consultant_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)
) -> dict:
    c = db.get(Consultant, consultant_id)
    if not c:
        raise HTTPException(404, "consultant not found")
    data = await file.read()
    text = extract_text(file.filename or "resume.txt", data)
    skills = extract_skills(text)
    resume = Resume(
        consultant_id=c.id, filename=file.filename or "resume.txt",
        content_text=text, parsed_skills=skills, is_primary=not c.resumes,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    ResumeAgent().process_resume(db, resume)
    # merge newly discovered skills into the consultant profile
    merged = list(dict.fromkeys([*c.skills, *skills]))
    c.skills = merged
    db.add(c)
    db.commit()
    return {"resume_id": resume.id, "filename": resume.filename,
            "parsed_skills": skills, "consultant_skills": merged}


# ── Matching ──
@router.get("/consultants/{consultant_id}/matches")
def consultant_matches(consultant_id: int, top_k: int = 5, db: Session = Depends(get_db)) -> dict:
    try:
        return MatchingAgent().match_consultant(db, consultant_id, top_k)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/jobs/{job_id}/candidates")
def job_candidates(job_id: int, top_k: int = 5, db: Session = Depends(get_db)) -> dict:
    try:
        return MatchingAgent().match_job(db, job_id, top_k)
    except ValueError as e:
        raise HTTPException(404, str(e))


# ── Submissions ──
class SubmissionRequest(BaseModel):
    consultant_id: int
    job_id: int
    vendor_id: int | None = None
    rate: float | None = None


@router.get("/submissions")
def list_submissions(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(select(Submission).order_by(Submission.created_at.desc())).all()
    return [submission_brief(s) for s in rows]


@router.post("/submissions")
def create_submission(req: SubmissionRequest, db: Session = Depends(get_db)) -> dict:
    try:
        return SubmissionAgent().submit(
            db, req.consultant_id, req.job_id, req.vendor_id, req.rate
        )
    except ValueError as e:
        raise HTTPException(400, str(e))


# ── Interviews ──
@router.post("/submissions/{submission_id}/interview")
def schedule_interview(submission_id: int, db: Session = Depends(get_db)) -> dict:
    try:
        return InterviewAgent().schedule(db, submission_id)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/followups")
def followups(db: Session = Depends(get_db)) -> dict:
    return FollowupAgent().run(db)
