"""Agent base contract + shared date helpers."""
from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session


class BaseAgent:
    name: str = "base"
    description: str = ""

    def run(self, db: Session, **kwargs):  # pragma: no cover - overridden
        raise NotImplementedError


def days_until(target: date | None, today: date | None = None) -> int | None:
    if target is None:
        return None
    today = today or date.today()
    return (target - today).days


def days_on_bench(bench_start: date | None, today: date | None = None) -> int:
    if bench_start is None:
        return 0
    today = today or date.today()
    return max(0, (today - bench_start).days)
