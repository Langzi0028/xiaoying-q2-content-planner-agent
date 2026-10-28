from __future__ import annotations

from content_planner.service import run_demo


def test_retryable_estimate_failure_preserves_script_and_recovers(tmp_path) -> None:
    result = run_demo(
        database_path=tmp_path / "planner.db",
        scenario="tool-failure",
        fail_tool="estimate_cost",
        fail_on_attempt=1,
    )

    estimate_results = [
        item for item in result.tool_results if item["tool_name"] == "estimate_cost"
    ]
    script_steps = [
        step for step in result.steps if step["step_type"] == "generate_script"
    ]

    assert result.status == "completed"
    assert len(script_steps) == 1
    assert script_steps[0]["status"] == "succeeded"
    assert [item["ok"] for item in estimate_results] == [False, True]
    assert [item["attempt"] for item in estimate_results] == [1, 2]
