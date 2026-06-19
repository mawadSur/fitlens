"""The 12-agent layer registry."""
from __future__ import annotations

from .analytics import PlacementAgent, RevenueAgent
from .base import BaseAgent
from .matching import MarketAgent, MatchingAgent, VendorAgent
from .outreach import FollowupAgent, InterviewAgent, MarketingAgent, SubmissionAgent
from .talent import BenchAgent, ImmigrationAgent, ResumeAgent

AGENT_CLASSES: list[type[BaseAgent]] = [
    BenchAgent,
    ResumeAgent,
    ImmigrationAgent,
    MarketAgent,
    MatchingAgent,
    VendorAgent,
    MarketingAgent,
    SubmissionAgent,
    FollowupAgent,
    InterviewAgent,
    PlacementAgent,
    RevenueAgent,
]

AGENTS: dict[str, BaseAgent] = {cls.name: cls() for cls in AGENT_CLASSES}


def get_agent(name: str) -> BaseAgent:
    if name not in AGENTS:
        raise KeyError(f"unknown agent '{name}'")
    return AGENTS[name]


def agent_catalog() -> list[dict]:
    return [{"name": a.name, "description": a.description} for a in AGENTS.values()]


__all__ = [
    "AGENT_CLASSES",
    "AGENTS",
    "BenchAgent",
    "ResumeAgent",
    "ImmigrationAgent",
    "MarketAgent",
    "MatchingAgent",
    "VendorAgent",
    "MarketingAgent",
    "SubmissionAgent",
    "FollowupAgent",
    "InterviewAgent",
    "PlacementAgent",
    "RevenueAgent",
    "agent_catalog",
    "get_agent",
]
