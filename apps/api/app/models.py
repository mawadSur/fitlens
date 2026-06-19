"""Domain model for FitLens Workforce Supply Intelligence."""
from __future__ import annotations

import enum
from datetime import date, datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class VisaStatus(str, enum.Enum):
    H1B = "H1B"
    OPT = "OPT"
    STEM_OPT = "STEM_OPT"
    GC = "GC"
    GC_EAD = "GC_EAD"
    USC = "USC"
    TN = "TN"
    L1 = "L1"
    H4_EAD = "H4_EAD"
    C2C = "C2C"
    W2 = "W2"


class ConsultantStatus(str, enum.Enum):
    AVAILABLE = "available"
    ON_PROJECT = "on_project"
    MARKETING = "marketing"
    PLACED = "placed"
    INACTIVE = "inactive"


class SubmissionStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    SHORTLISTED = "shortlisted"
    INTERVIEW = "interview"
    OFFER = "offer"
    PLACED = "placed"
    REJECTED = "rejected"


class Consultant(Base):
    __tablename__ = "consultants"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    email: Mapped[str] = mapped_column(String(160), unique=True)
    phone: Mapped[str] = mapped_column(String(40), default="")
    visa_status: Mapped[VisaStatus] = mapped_column(Enum(VisaStatus))
    status: Mapped[ConsultantStatus] = mapped_column(
        Enum(ConsultantStatus), default=ConsultantStatus.ON_PROJECT
    )
    location: Mapped[str] = mapped_column(String(120), default="")
    willing_to_relocate: Mapped[bool] = mapped_column(Boolean, default=True)
    primary_skill: Mapped[str] = mapped_column(String(120), default="")
    skills: Mapped[list] = mapped_column(JSON, default=list)
    years_experience: Mapped[float] = mapped_column(Float, default=0.0)
    expected_rate: Mapped[float] = mapped_column(Float, default=0.0)  # $/hr
    daily_bench_cost: Mapped[float] = mapped_column(Float, default=0.0)  # $/day while benched
    availability_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    bench_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    resumes: Mapped[list["Resume"]] = relationship(back_populates="consultant", cascade="all, delete-orphan")
    immigration: Mapped["ImmigrationRecord | None"] = relationship(
        back_populates="consultant", uselist=False, cascade="all, delete-orphan"
    )
    submissions: Mapped[list["Submission"]] = relationship(back_populates="consultant")


class ImmigrationRecord(Base):
    __tablename__ = "immigration_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    consultant_id: Mapped[int] = mapped_column(ForeignKey("consultants.id"))
    visa_type: Mapped[VisaStatus] = mapped_column(Enum(VisaStatus))
    work_auth_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    work_auth_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    ead_expiry: Mapped[date | None] = mapped_column(Date, nullable=True)
    i94_expiry: Mapped[date | None] = mapped_column(Date, nullable=True)
    lca_filed: Mapped[bool] = mapped_column(Boolean, default=False)
    worksite_location: Mapped[str] = mapped_column(String(120), default="")
    notes: Mapped[str] = mapped_column(Text, default="")

    consultant: Mapped["Consultant"] = relationship(back_populates="immigration")


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(primary_key=True)
    consultant_id: Mapped[int] = mapped_column(ForeignKey("consultants.id"))
    filename: Mapped[str] = mapped_column(String(255))
    content_text: Mapped[str] = mapped_column(Text, default="")
    parsed_skills: Mapped[list] = mapped_column(JSON, default=list)
    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    consultant: Mapped["Consultant"] = relationship(back_populates="resumes")


class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    contact_email: Mapped[str] = mapped_column(String(160), default="")
    tier: Mapped[str] = mapped_column(String(20), default="B")  # A/B/C
    response_rate: Mapped[float] = mapped_column(Float, default=0.0)  # 0..1
    avg_response_hours: Mapped[float] = mapped_column(Float, default=48.0)
    placements_count: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[float] = mapped_column(Float, default=0.0)  # 0..100
    last_contacted: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    jobs: Mapped[list["Job"]] = relationship(back_populates="vendor")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    client: Mapped[str] = mapped_column(String(160), default="")
    vendor_id: Mapped[int | None] = mapped_column(ForeignKey("vendors.id"), nullable=True)
    location: Mapped[str] = mapped_column(String(120), default="")
    remote: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[str] = mapped_column(Text, default="")
    required_skills: Mapped[list] = mapped_column(JSON, default=list)
    min_rate: Mapped[float] = mapped_column(Float, default=0.0)
    max_rate: Mapped[float] = mapped_column(Float, default=0.0)
    visa_requirements: Mapped[list] = mapped_column(JSON, default=list)  # allowed visa types
    source: Mapped[str] = mapped_column(String(40), default="manual")
    external_id: Mapped[str] = mapped_column(String(120), default="")
    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="open")
    posted_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    vendor: Mapped["Vendor | None"] = relationship(back_populates="jobs")


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    consultant_id: Mapped[int] = mapped_column(ForeignKey("consultants.id"))
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"))
    vendor_id: Mapped[int | None] = mapped_column(ForeignKey("vendors.id"), nullable=True)
    rate: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[SubmissionStatus] = mapped_column(
        Enum(SubmissionStatus), default=SubmissionStatus.DRAFT
    )
    match_score: Mapped[float] = mapped_column(Float, default=0.0)
    rtr_signed: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str] = mapped_column(Text, default="")
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    consultant: Mapped["Consultant"] = relationship(back_populates="submissions")
    job: Mapped["Job"] = relationship()
    interviews: Mapped[list["Interview"]] = relationship(
        back_populates="submission", cascade="all, delete-orphan"
    )


class Interview(Base):
    __tablename__ = "interviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id"))
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    mode: Mapped[str] = mapped_column(String(20), default="video")  # video/phone/onsite
    status: Mapped[str] = mapped_column(String(20), default="proposed")
    panel: Mapped[str] = mapped_column(String(200), default="")
    notes: Mapped[str] = mapped_column(Text, default="")

    submission: Mapped["Submission"] = relationship(back_populates="interviews")


class RateCard(Base):
    __tablename__ = "rate_cards"

    id: Mapped[int] = mapped_column(primary_key=True)
    skill: Mapped[str] = mapped_column(String(120))
    region: Mapped[str] = mapped_column(String(80), default="US")
    min_rate: Mapped[float] = mapped_column(Float, default=0.0)
    max_rate: Mapped[float] = mapped_column(Float, default=0.0)
    demand_score: Mapped[float] = mapped_column(Float, default=50.0)  # 0..100


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(160), unique=True)
    name: Mapped[str] = mapped_column(String(160), default="")
    # Stored as a string (not an Enum) to avoid enum-migration friction; see auth.Role.
    role: Mapped[str] = mapped_column(String(40), default="viewer")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
