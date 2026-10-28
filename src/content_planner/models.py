"""Small immutable result models exposed by the command-line application."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    name: str
    asset_id: str
    base_cost: int
    duration_minutes: int


@dataclass
class PlanningResult:
    run_id: str
    status: str
    topic: str
    budget: int
    deadline: str
    idempotency_key: str | None = None
    selected_candidate_id: str | None = None
    actual_cost: int = 0
    estimated_duration_minutes: int = 0
    saved_plan_id: str | None = None
    replan_count: int = 0
    rejected_candidate_ids: list[str] = field(default_factory=list)
    failure_reason: dict[str, str] | None = None
    planner_mode: str = "rule"
    steps: list[dict[str, Any]] = field(default_factory=list)
    tool_results: list[dict[str, Any]] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    trace: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
