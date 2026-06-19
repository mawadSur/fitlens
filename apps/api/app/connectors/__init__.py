"""Connector registry + aggregate status (powers the dashboard's integration panel)."""
from __future__ import annotations

from .base import ConnectorStatus
from .comms import COMMS, EmailConnector, TeamsConnector
from .jobsources import JOB_SOURCES

ALL_CONNECTORS = [*JOB_SOURCES, *COMMS]


def connector_status() -> list[ConnectorStatus]:
    return [cls().status() for cls in ALL_CONNECTORS]


def get_email_connector() -> EmailConnector:
    return EmailConnector()


__all__ = [
    "ALL_CONNECTORS",
    "ConnectorStatus",
    "EmailConnector",
    "TeamsConnector",
    "connector_status",
    "get_email_connector",
    "JOB_SOURCES",
]
