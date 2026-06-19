"""Connector base. A connector is LIVE when all its required credentials are
present; otherwise it runs in MOCK mode and says so. This is the honest way to
ship 'real integrations' without inventing third-party accounts."""
from __future__ import annotations

from dataclasses import dataclass, field

from ..config import settings


@dataclass
class ConnectorStatus:
    name: str
    category: str
    live: bool
    missing_credentials: list[str] = field(default_factory=list)
    note: str = ""


class BaseConnector:
    name: str = "base"
    category: str = "generic"
    required_env: list[str] = []
    note: str = ""

    @property
    def is_live(self) -> bool:
        return all(getattr(settings, key, "") for key in self.required_env)

    def status(self) -> ConnectorStatus:
        missing = [k for k in self.required_env if not getattr(settings, k, "")]
        return ConnectorStatus(
            name=self.name,
            category=self.category,
            live=self.is_live,
            missing_credentials=missing,
            note=self.note,
        )
