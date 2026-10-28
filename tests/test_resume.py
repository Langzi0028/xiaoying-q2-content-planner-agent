from __future__ import annotations

from content_planner.service import resume_run, run_demo


def test_resume_returns_completed_run_without_repeating_successful_steps(tmp_path) -> None:
    database_path = tmp_path / "planner.db"
    first = run_demo(
        database_path=database_path,
        scenario="tool-failure",
        fail_tool="estimate_cost",
        fail_on_attempt=1,
    )
    second = resume_run(database_path=database_path, run_id=first.run_id)

    assert first.status == "completed"
    assert second.run_id == first.run_id
    assert second.tool_results == first.tool_results
    assert second.trace == first.trace


def test_resume_returns_partial_run_without_repeating_tools(tmp_path) -> None:
    database_path = tmp_path / "planner.db"
    first = run_demo(
        database_path=database_path,
        scenario="no-feasible-plan",
    )
    second = resume_run(database_path=database_path, run_id=first.run_id)

    assert first.status == "partial"
    assert second.tool_results == first.tool_results


def test_resume_rejects_unknown_run(tmp_path) -> None:
    from pytest import raises

    with raises(ValueError, match="RUN_NOT_FOUND"):
        resume_run(database_path=tmp_path / "planner.db", run_id="missing")


def test_resume_continues_interrupted_run_without_repeating_script(tmp_path) -> None:
    database_path = tmp_path / "planner.db"
    interrupted = run_demo(
        database_path=database_path,
        scenario="over-budget-replan",
        interrupt_before="estimate_cost",
    )

    assert interrupted.status == "running"
    assert len(
        [step for step in interrupted.steps if step["step_type"] == "generate_script"]
    ) == 1

    resumed = resume_run(database_path=database_path, run_id=interrupted.run_id)

    assert resumed.status == "completed"
    assert resumed.selected_candidate_id == "candidate_low_cost"
    assert len(
        [step for step in resumed.steps if step["step_type"] == "generate_script"]
    ) == 2
    assert any(entry["action"] == "resume_execution" for entry in resumed.trace)
