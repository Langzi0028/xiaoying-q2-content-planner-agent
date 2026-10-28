from __future__ import annotations

import sqlite3

from content_planner.service import run_request


def test_missing_budget_request_is_blocked_without_persisting_or_calling_tools(tmp_path) -> None:
    result = run_request(
        database_path=tmp_path / "planner.db",
        topic="夏季防晒新品活动",
        budget=None,
        deadline="2030-10-30T18:00:00+08:00",
    )

    assert result.status == "blocked"
    assert result.failure_reason == {"code": "MISSING_BUDGET"}
    assert result.tool_results == []


def test_run_request_with_valid_input_uses_graph_and_completes(tmp_path) -> None:
    database_path = tmp_path / "planner.db"
    result = run_request(
        database_path=database_path,
        topic="夏季防晒新品活动",
        budget=10,
        deadline="2030-10-30T18:00:00+08:00",
    )

    assert result.status == "completed"
    assert result.actual_cost == 8
    assert result.topic == "夏季防晒新品活动"
    assert result.budget == 10
    assert result.deadline == "2030-10-30T18:00:00+08:00"
    checkpoint_rows = sqlite3.connect(database_path).execute(
        "SELECT COUNT(*) FROM checkpoints"
    ).fetchone()[0]
    assert checkpoint_rows > 0
