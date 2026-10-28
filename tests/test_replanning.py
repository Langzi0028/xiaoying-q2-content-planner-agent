from __future__ import annotations

from content_planner.service import run_demo


def test_over_budget_candidate_is_replanned_to_affordable_candidate(tmp_path) -> None:
    result = run_demo(
        database_path=tmp_path / "planner.db",
        scenario="over-budget-replan",
    )

    assert result.status == "completed"
    assert result.selected_candidate_id == "candidate_low_cost"
    assert result.actual_cost == 8
    assert result.saved_plan_id is not None
    assert result.replan_count == 1
    assert result.rejected_candidate_ids == ["candidate_premium"]
