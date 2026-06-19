"""FitLens Workforce Supply Intelligence — FastAPI application."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .observability import RequestIDMiddleware, configure_logging
from .routers import auth as auth_router
from .routers import consultants, dashboard, jobs, workflow
from .seed import reset_and_seed


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    reset_and_seed()  # idempotent dev bootstrap
    yield


app = FastAPI(
    title="FitLens Workforce Supply Intelligence",
    version="0.1.0",
    description="Agentic Workforce Operating System — bench monitoring, matching, submission, forecasting.",
    lifespan=lifespan,
)

app.add_middleware(RequestIDMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.web_origin, "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(consultants.router)
app.include_router(jobs.router)
app.include_router(workflow.router)
app.include_router(dashboard.router)
app.include_router(auth_router.router)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "fitlens-api", "environment": settings.environment}
