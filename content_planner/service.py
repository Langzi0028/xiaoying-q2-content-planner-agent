"""Deterministic application service used by the CLI and graph workflow."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from content_planner.enums import RunStatus, StepStatus
from content_planner.fixtures.scenarios import (
    OVER_BUDGET_REPLAN_CANDIDATES,
)
from content_planner.models import Candidate, PlanningResult
from content_planner.storage.repositories import PlannerRepository
from content_planner.validation import validate_request


def run_demo(
    *,
    database_path: Path | str,
    scenario: str,
    fail_tool: str | None = None,
    fail_on_attempt: int | None = None,
    interrupt_before: str | None = None,
    idempotency_key: str | None = None,
) -> PlanningResult:
    """Run a reproducible rule-driven scenario for assessment verification."""
    if idempotency_key:
        repository = PlannerRepository(database_path)
        existing = repository.get_run_by_idempotency_key(idempotency_key)
        if existing:
            return repository.get_run(existing.run_id) or existing
    from content_planner.graph.workflow import invoke_scenario

    run_id = f"run_{uuid4().hex[:12]}"
    final_state = invoke_scenario(
        database_path=database_path,
        scenario=scenario,
        thread_id=run_id,
        run_id=run_id,
        fail_tool=fail_tool,
        fail_on_attempt=fail_on_attempt,
        interrupt_before=interrupt_before,
        idempotency_key=idempotency_key,
    )
    if "result" not in final_state:
        return _read_interrupted_state(final_state) or load_run(
            database_path=database_path, run_id=run_id
        ) or _new_result(run_id=run_id)
    return PlanningResult(**final_state["result"])


def run_request(
    *,
    database_path: Path | str,
    topic: str | None,
    budget: int | None,
    deadline: str | None,
    idempotency_key: str | None = None,
) -> PlanningResult:
    """Validate a CLI request before dispatching the LangGraph workflow."""
    validation = validate_request(topic=topic, budget=budget, deadline=deadline)
    if not validation.is_valid:
        return PlanningResult(
            run_id=f"run_{uuid4().hex[:12]}",
            status=validation.status,
            topic=topic or "",
            budget=budget or 0,
            deadline=deadline or "",
            idempotency_key=idempotency_key,
            failure_reason={"code": validation.error_code or "VALIDATION_ERROR"},
        )
    if idempotency_key:
        repository = PlannerRepository(database_path)
        existing = repository.get_run_by_idempotency_key(idempotency_key)
        if existing:
            return repository.get_run(existing.run_id) or existing
    from content_planner.graph.workflow import invoke_scenario

    run_id = f"run_{uuid4().hex[:12]}"
    final_state = invoke_scenario(
        database_path=database_path,
        scenario="over-budget-replan",
        thread_id=run_id,
        run_id=run_id,
        topic=topic,
        budget=budget,
        deadline=deadline,
        idempotency_key=idempotency_key,
    )
    return PlanningResult(**final_state["result"])


def _read_interrupted_state(final_state: dict) -> PlanningResult | None:
    result = final_state.get("result_object")
    return result if isinstance(result, PlanningResult) else None


def load_run(*, database_path: Path | str, run_id: str) -> PlanningResult | None:
    """Read a persisted audit record without re-running tools."""
    return PlannerRepository(database_path).get_run(run_id)


def resume_run(
    *,
    database_path: Path | str,
    run_id: str,
) -> PlanningResult:
    """Resume an unfinished run or return a completed run without duplicate tools."""
    existing = load_run(database_path=database_path, run_id=run_id)
    if existing is not None:
        if existing.status == RunStatus.RUNNING:
            return _resume_interrupted_run(
                database_path=database_path,
                existing=existing,
            )
        return existing
    raise ValueError("RUN_NOT_FOUND")


def _resume_interrupted_run(
    *, database_path: Path | str, existing: PlanningResult
) -> PlanningResult:
    """Continue from the persisted pre-estimate boundary without replaying scripts."""
    repository = PlannerRepository(database_path)
    completed_estimates = {
        step["step_id"]
        for step in existing.steps
        if step["step_type"] == "estimate_cost" and step["status"] == StepStatus.SUCCEEDED
    }
    candidates = list(OVER_BUDGET_REPLAN_CANDIDATES)
    selected = candidates[0]
    if f"estimate_cost:{selected.candidate_id}" not in completed_estimates:
        _estimate_candidate(repository, existing, selected)

    if selected.base_cost > existing.budget:
        replacement = candidates[1]
        repository.record_replan(
            existing,
            rejected_candidate_id=selected.candidate_id,
            selected_candidate_id=replacement.candidate_id,
            reason="BUDGET_EXCEEDED",
        )
        existing.events.append(
            {
                "type": "replan",
                "reason": "BUDGET_EXCEEDED",
                "from_candidate_id": selected.candidate_id,
                "to_candidate_id": replacement.candidate_id,
                "planner_mode": "rule",
            }
        )
        _generate_script(repository, existing, replacement)
        _estimate_candidate(repository, existing, replacement)
        selected = replacement

    repository.record_trace(
        existing,
        node="resume",
        action="resume_execution",
        parameters={"run_id": existing.run_id},
        result_summary="Resumed after preserving already successful script artifacts.",
        next_action="save_plan",
        rationale="The interrupted run paused before cost estimation, so no script is replayed.",
        decision_source="rule",
    )
    _complete_with_saved_plan(repository, existing, selected)
    return existing


def _new_result(
    idempotency_key: str | None = None,
    *,
    run_id: str | None = None,
    topic: str | None = None,
    budget: int | None = None,
    deadline: str | None = None,
) -> PlanningResult:
    return PlanningResult(
        run_id=run_id or f"run_{uuid4().hex[:12]}",
        status=RunStatus.RUNNING,
        topic=topic or "夏季防晒新品活动",
        budget=budget if budget is not None else 10,
        deadline=deadline or "2030-10-30T18:00:00+08:00",
        idempotency_key=idempotency_key,
    )


def _record_asset_search(
    repository: PlannerRepository, result: PlanningResult, candidates: list[Candidate]
) -> None:
    repository.record_step(
        result,
        step_id="search_assets",
        step_type="search_assets",
        status=StepStatus.SUCCEEDED,
        dependencies=[],
        output={"candidate_ids": [candidate.candidate_id for candidate in candidates]},
    )
    repository.record_tool_result(
        result,
        step_id="search_assets",
        tool_name="search_assets",
        attempt=1,
        ok=True,
        payload={"candidate_count": len(candidates)},
    )


def _generate_script(
    repository: PlannerRepository, result: PlanningResult, candidate: Candidate
) -> None:
    step_id = f"generate_script:{candidate.candidate_id}"
    output = {
        "candidate_id": candidate.candidate_id,
        "script_id": f"script_{candidate.candidate_id}",
        "content": f"围绕{result.topic}的{candidate.name}脚本",
    }
    repository.record_step(
        result,
        step_id=step_id,
        step_type="generate_script",
        status=StepStatus.SUCCEEDED,
        dependencies=["search_assets"],
        output=output,
    )
    repository.record_tool_result(
        result,
        step_id=step_id,
        tool_name="generate_script",
        attempt=1,
        ok=True,
        payload=output,
    )


def _estimate_candidate(
    repository: PlannerRepository,
    result: PlanningResult,
    candidate: Candidate,
    *,
    attempt: int = 1,
) -> None:
    step_id = f"estimate_cost:{candidate.candidate_id}"
    output = {
        "candidate_id": candidate.candidate_id,
        "total_cost": candidate.base_cost,
        "duration_minutes": candidate.duration_minutes,
    }
    repository.record_step(
        result,
        step_id=step_id,
        step_type="estimate_cost",
        status=StepStatus.SUCCEEDED,
        dependencies=[f"generate_script:{candidate.candidate_id}"],
        output=output,
    )
    repository.record_tool_result(
        result,
        step_id=step_id,
        tool_name="estimate_cost",
        attempt=attempt,
        ok=True,
        payload=output,
    )


def _record_estimate_failure(
    repository: PlannerRepository,
    result: PlanningResult,
    candidate: Candidate,
    *,
    attempt: int,
) -> None:
    step_id = f"estimate_cost:{candidate.candidate_id}"
    error = {
        "code": "TOOL_UNAVAILABLE",
        "message": "成本估算服务暂时不可用",
        "retryable": True,
    }
    repository.record_step(
        result,
        step_id=step_id,
        step_type="estimate_cost",
        status=StepStatus.FAILED,
        dependencies=[f"generate_script:{candidate.candidate_id}"],
        error=error,
    )
    repository.record_tool_result(
        result,
        step_id=step_id,
        tool_name="estimate_cost",
        attempt=attempt,
        ok=False,
        error=error,
    )


def _complete_with_saved_plan(
    repository: PlannerRepository, result: PlanningResult, candidate: Candidate
) -> None:
    result.selected_candidate_id = candidate.candidate_id
    result.actual_cost = candidate.base_cost
    result.estimated_duration_minutes = candidate.duration_minutes
    _save_verified_plan(repository, result, candidate)
    result.status = RunStatus.COMPLETED
    repository.update_run(result)


def _save_verified_plan(
    repository: PlannerRepository, result: PlanningResult, candidate: Candidate
) -> None:
    if candidate.base_cost > result.budget:
        raise ValueError("Cannot save a plan that exceeds its budget")

    step_id = "save_plan"
    content = {
        "topic": result.topic,
        "candidate_id": candidate.candidate_id,
        "candidate_name": candidate.name,
        "cost": candidate.base_cost,
    }
    result.saved_plan_id = repository.save_plan(result, content)
    repository.record_step(
        result,
        step_id=step_id,
        step_type="save_plan",
        status=StepStatus.SUCCEEDED,
        dependencies=[f"estimate_cost:{candidate.candidate_id}"],
        output={"plan_id": result.saved_plan_id},
    )
    repository.record_tool_result(
        result,
        step_id=step_id,
        tool_name="save_plan",
        attempt=1,
        ok=True,
        payload={"plan_id": result.saved_plan_id},
    )
