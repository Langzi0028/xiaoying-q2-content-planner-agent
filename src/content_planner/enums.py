"""Domain statuses and error codes."""

from __future__ import annotations

from enum import StrEnum


class RunStatus(StrEnum):
    DRAFT = "draft"
    RUNNING = "running"
    REPLANNING = "replanning"
    COMPLETED = "completed"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    FAILED = "failed"


class StepStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"
