from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..agents import (
    BenchAgent,
    ImmigrationAgent,
    MarketAgent,
    PlacementAgent,
    RevenueAgent,
    agent_catalog,
    get_agent,
)
from ..connectors import connector_status
from ..db import get_db
from ..embeddings import get_embedder
from ..models import Consultant, Interview, Job, Submission, SubmissionStatus

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)) -> dict:
    bench = BenchAgent().run(db)
    revenue = RevenueAgent().run(db)
    placement = PlacementAgent().run(db)
    immigration = ImmigrationAgent().run(db)
    counts = {
        "consultants": db.scalar(select(func.count(Consultant.id))),
        "open_jobs": db.scalar(select(func.count(Job.id)).where(Job.status == "open")),
        "submissions": db.scalar(select(func.count(Submission.id))),
        "placements": db.scalar(
            select(func.count(Submission.id)).where(Submission.status == SubmissionStatus.PLACED)
        ),
        "interviews": db.scalar(select(func.count(Interview.id))),
    }
    return {
        "counts": counts,
        "hot_bench": bench["hot_bench"],
        "bench_alerts": bench["alerts"],
        "total_daily_bench_cost": bench["total_daily_bench_cost"],
        "immigration_alerts": immigration["alerts"],
        "revenue_forecast": revenue,
        "top_placements": placement["predictions"][:5],
    }


@router.get("/agents")
def agents() -> dict:
    return {"agents": agent_catalog(), "count": len(agent_catalog())}


@router.post("/agents/{name}/run")
def run_agent(name: str, params: dict[str, Any] | None = None, db: Session = Depends(get_db)) -> dict:
    try:
        agent = get_agent(name)
    except KeyError as e:
        raise HTTPException(404, str(e))
    try:
        result = agent.run(db, **(params or {}))
    except (ValueError, TypeError) as e:
        raise HTTPException(400, str(e))
    return {"agent": name, "result": result}


@router.get("/market")
def market(skill: str | None = None, db: Session = Depends(get_db)) -> dict:
    return MarketAgent().run(db, skill=skill)


@router.get("/immigration")
def immigration(db: Session = Depends(get_db)) -> dict:
    return ImmigrationAgent().run(db)


@router.get("/placement")
def placement(db: Session = Depends(get_db)) -> dict:
    return PlacementAgent().run(db)


@router.get("/revenue")
def revenue(db: Session = Depends(get_db)) -> dict:
    return RevenueAgent().run(db)


@router.get("/integrations")
def integrations() -> dict:
    statuses = [s.__dict__ for s in connector_status()]
    return {
        "embedder_backend": getattr(get_embedder(), "backend", "unknown"),
        "connectors": statuses,
        "live_count": sum(1 for s in statuses if s["live"]),
        "total": len(statuses),
    }
