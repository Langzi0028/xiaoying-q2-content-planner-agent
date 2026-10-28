"""Input validation for planning requests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    status: str
    error_code: str | None = None


def validate_request(
    *, topic: str | None, budget: float | None, deadline: str | None
) -> ValidationResult:
    """Validate required user inputs before invoking any planning tools."""
    if topic is None or not topic.strip():
        return ValidationResult(False, "blocked", "MISSING_TOPIC")
    if budget is None:
        return ValidationResult(False, "blocked", "MISSING_BUDGET")
    if deadline is None or not deadline.strip():
        return ValidationResult(False, "blocked", "MISSING_DEADLINE")
    if budget <= 0:
        return ValidationResult(False, "blocked", "INVALID_BUDGET")
    try:
        parsed_deadline = datetime.fromisoformat(deadline)
    except ValueError:
        return ValidationResult(False, "blocked", "INVALID_DEADLINE")
    if parsed_deadline.tzinfo is None:
        return ValidationResult(False, "blocked", "INVALID_DEADLINE")
    if parsed_deadline <= datetime.now(timezone.utc):
        return ValidationResult(False, "blocked", "INVALID_DEADLINE")
    return ValidationResult(True, "draft")
