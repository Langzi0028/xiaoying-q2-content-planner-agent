from __future__ import annotations

from content_planner.service import run_demo, run_request


def test_same_idempotency_key_returns_the_existing_run_without_new_tool_calls(tmp_path) -> None:
    database_path = tmp_path / "planner.db"

    first = run_demo(
        database_path=database_path,
        scenario="over-budget-replan",
        idempotency_key="assessment-case-1",
    )
    second = run_demo(
        database_path=database_path,
        scenario="over-budget-replan",
        idempotency_key="assessment-case-1",
    )

    assert second.run_id == first.run_id
    assert second.tool_results == first.tool_results
    assert second.trace == first.trace
    assert second.trace


def test_request_idempotency_returns_existing_graph_run_without_constraint_error(tmp_path) -> None:
    database_path = tmp_path / "planner.db"
    first = run_request(
        database_path=database_path,
        topic="夏季防晒新品活动",
        budget=10,
        deadline="2030-10-30T18:00:00+08:00",
        idempotency_key="request-key-1",
    )
    second = run_request(
        database_path=database_path,
        topic="夏季防晒新品活动",
        budget=10,
        deadline="2030-10-30T18:00:00+08:00",
        idempotency_key="request-key-1",
    )

    assert first.status == "completed"
    assert second.run_id == first.run_id
    assert second.trace == first.trace
