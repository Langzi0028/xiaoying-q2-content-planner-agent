from __future__ import annotations

from content_planner.service import run_demo


def test_deadline_violation_replans_to_faster_candidate(tmp_path) -> None:
    result = run_demo(
        database_path=tmp_path / "planner.db",
        scenario="deadline-replan",
    )

    assert result.status == "completed"
    assert result.selected_candidate_id == "candidate_fast"
    assert result.rejected_candidate_ids == ["candidate_slow"]
    assert result.estimated_duration_minutes == 30
