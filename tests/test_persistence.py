from __future__ import annotations

import sqlite3

from content_planner.service import run_demo


def test_over_budget_run_persists_steps_tools_replan_and_saved_plan(tmp_path) -> None:
    database_path = tmp_path / "planner.db"
    result = run_demo(database_path=database_path, scenario="over-budget-replan")

    connection = sqlite3.connect(database_path)
    step_count = connection.execute(
        "SELECT COUNT(*) FROM steps WHERE run_id = ?", (result.run_id,)
    ).fetchone()[0]
    tool_count = connection.execute(
        "SELECT COUNT(*) FROM tool_results WHERE run_id = ?", (result.run_id,)
    ).fetchone()[0]
    replan_count = connection.execute(
        "SELECT COUNT(*) FROM replans WHERE run_id = ?", (result.run_id,)
    ).fetchone()[0]
    saved_plan_count = connection.execute(
        "SELECT COUNT(*) FROM saved_plans WHERE run_id = ?", (result.run_id,)
    ).fetchone()[0]

    assert step_count == 6
    assert tool_count == 6
    assert replan_count == 1
    assert saved_plan_count == 1
