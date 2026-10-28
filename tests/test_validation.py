from __future__ import annotations

from datetime import datetime, timedelta, timezone

from content_planner.validation import validate_request


def test_missing_budget_blocks_without_tool_calls() -> None:
    result = validate_request(
        topic="夏季防晒新品活动",
        budget=None,
        deadline="2030-10-30T18:00:00+08:00",
    )

    assert result.is_valid is False
    assert result.status == "blocked"
    assert result.error_code == "MISSING_BUDGET"


def test_missing_topic_blocks_without_tool_calls() -> None:
    result = validate_request(
        topic=" ",
        budget=10,
        deadline="2030-10-30T18:00:00+08:00",
    )

    assert result.is_valid is False
    assert result.status == "blocked"
    assert result.error_code == "MISSING_TOPIC"


def test_missing_deadline_blocks_without_tool_calls() -> None:
    result = validate_request(
        topic="夏季防晒新品活动",
        budget=10,
        deadline=None,
    )

    assert result.is_valid is False
    assert result.status == "blocked"
    assert result.error_code == "MISSING_DEADLINE"


def test_non_positive_budget_blocks_without_tool_calls() -> None:
    result = validate_request(
        topic="夏季防晒新品活动",
        budget=0,
        deadline="2030-10-30T18:00:00+08:00",
    )

    assert result.is_valid is False
    assert result.status == "blocked"
    assert result.error_code == "INVALID_BUDGET"


def test_past_deadline_blocks_without_tool_calls() -> None:
    past_deadline = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    result = validate_request(topic="夏季防晒新品活动", budget=10, deadline=past_deadline)

    assert result.is_valid is False
    assert result.status == "blocked"
    assert result.error_code == "INVALID_DEADLINE"


def test_malformed_deadline_blocks_without_tool_calls() -> None:
    result = validate_request(topic="夏季防晒新品活动", budget=10, deadline="tomorrow")

    assert result.is_valid is False
    assert result.status == "blocked"
    assert result.error_code == "INVALID_DEADLINE"
