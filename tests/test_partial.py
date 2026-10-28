from __future__ import annotations

from content_planner.service import run_demo


def test_no_feasible_plan_is_not_saved_and_reports_budget_gap(tmp_path) -> None:
    result = run_demo(
        database_path=tmp_path / "planner.db",
        scenario="no-feasible-plan",
    )

    assert result.status == "partial"
    assert result.saved_plan_id is None
    assert result.failure_reason == {
        "code": "NO_FEASIBLE_PLAN",
        "minimum_cost": "12",
        "budget_gap": "2",
    }
