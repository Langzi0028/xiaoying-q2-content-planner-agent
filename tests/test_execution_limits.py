from __future__ import annotations

from content_planner.graph.workflow import invoke_scenario


def test_tool_call_limit_returns_partial_result_without_saving(tmp_path) -> None:
    final_state = invoke_scenario(
        database_path=tmp_path / "planner.db",
        scenario="over-budget-replan",
        thread_id="tool-limit-case",
        max_tool_calls=1,
    )
    result = final_state["result"]

    assert result["status"] == "partial"
    assert result["saved_plan_id"] is None
    assert result["failure_reason"] == {
        "code": "EXECUTION_LIMIT_REACHED",
        "limit_type": "tool_calls",
        "limit": "1",
    }
    assert any(
        entry["node"] == "execution_guard" and entry["next_action"] == "finalize"
        for entry in result["trace"]
    )
