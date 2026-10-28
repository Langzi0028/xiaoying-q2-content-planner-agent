from __future__ import annotations

from content_planner.service import load_run, run_demo


REQUIRED_TRACE_FIELDS = {
    "sequence",
    "node",
    "action",
    "parameters",
    "result_summary",
    "next_action",
    "rationale",
    "decision_source",
}


def test_completed_run_contains_a_safe_decision_trace(tmp_path) -> None:
    result = run_demo(
        database_path=tmp_path / "planner.db",
        scenario="over-budget-replan",
    )

    assert result.trace
    assert all(REQUIRED_TRACE_FIELDS <= entry.keys() for entry in result.trace)
    assert any(entry["node"] == "decide_replan" for entry in result.trace)
    assert any(entry["action"] == "estimate_cost" for entry in result.trace)
    assert {entry["decision_source"] for entry in result.trace} <= {"rule", "fallback"}


def test_show_loads_persisted_trace_records(tmp_path) -> None:
    database_path = tmp_path / "planner.db"
    created = run_demo(database_path=database_path, scenario="tool-failure")

    loaded = load_run(database_path=database_path, run_id=created.run_id)

    assert loaded is not None
    assert loaded.trace == created.trace
