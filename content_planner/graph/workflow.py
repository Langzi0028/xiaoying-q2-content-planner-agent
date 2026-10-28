"""LangGraph state machine for planning, recovery, and auditable decisions."""

from __future__ import annotations

from pathlib import Path
from typing import NotRequired, TypedDict

from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from content_planner.config import load_llm_config
from content_planner.enums import RunStatus
from content_planner.fixtures.scenarios import (
    DEADLINE_REPLAN_CANDIDATES,
    NO_FEASIBLE_CANDIDATES,
    OVER_BUDGET_REPLAN_CANDIDATES,
    TOOL_FAILURE_CANDIDATES,
)
from content_planner.llm.client import build_decision_model
from content_planner.llm.decision_tools import extract_candidate_choice
from content_planner.models import Candidate, PlanningResult
from content_planner.service import (
    _complete_with_saved_plan,
    _estimate_candidate,
    _generate_script,
    _new_result,
    _record_asset_search,
    _record_estimate_failure,
)
from content_planner.storage.checkpoints import build_checkpointer
from content_planner.storage.repositories import PlannerRepository


DEFAULT_MAX_TOOL_CALLS = 12


class GraphState(TypedDict):
    scenario: str
    fail_tool: NotRequired[str | None]
    fail_on_attempt: NotRequired[int | None]
    result_object: NotRequired[PlanningResult]
    candidates: NotRequired[list[Candidate]]
    selected_index: NotRequired[int]
    estimate_attempt: NotRequired[int]
    last_estimate_failed: NotRequired[bool]
    next_route: NotRequired[str]
    replan_reason: NotRequired[str]
    result: NotRequired[dict]
    requested_run_id: NotRequired[str | None]
    requested_topic: NotRequired[str | None]
    requested_budget: NotRequired[int | None]
    requested_deadline: NotRequired[str | None]
    requested_idempotency_key: NotRequired[str | None]
    max_tool_calls: NotRequired[int]
    tool_call_count: NotRequired[int]
    interrupt_before: NotRequired[str | None]


def build_workflow(database_path: Path | str):
    """Compile one bounded LangGraph workflow backed by one audit database."""
    database_path = Path(database_path)
    audit_repository = PlannerRepository(database_path)

    def trace(result: PlanningResult, **entry: object) -> None:
        audit_repository.record_trace(result, **entry)

    def initialize(state: GraphState) -> dict:
        idempotency_key = state.get("requested_idempotency_key")
        if idempotency_key:
            existing = audit_repository.get_run_by_idempotency_key(idempotency_key)
            if existing:
                return {
                    "result_object": audit_repository.get_run(existing.run_id) or existing,
                    "next_route": "finalize",
                }
        result = _new_result(
            idempotency_key=state.get("requested_idempotency_key"),
            run_id=state.get("requested_run_id"),
            topic=state.get("requested_topic"),
            budget=state.get("requested_budget"),
            deadline=state.get("requested_deadline"),
        )
        audit_repository.create_run(result)
        trace(
            result,
            node="initialize",
            action="create_run",
            parameters={"scenario": state["scenario"]},
            result_summary="Created an auditable planning run.",
            next_action="search_assets",
            rationale="A valid run needs candidate assets before planning can continue.",
            decision_source="rule",
        )
        return {
            "result_object": result,
            "selected_index": 0,
            "estimate_attempt": 1,
            "last_estimate_failed": False,
            "tool_call_count": 0,
            "max_tool_calls": state.get("max_tool_calls", DEFAULT_MAX_TOOL_CALLS),
        }

    def search_assets(state: GraphState) -> dict:
        if limit_reached(state, "search_assets"):
            return {"next_route": "finish"}
        candidates = _candidates_for_scenario(state["scenario"])
        _record_asset_search(audit_repository, state["result_object"], candidates)
        trace(
            state["result_object"],
            node="search_assets",
            action="search_assets",
            parameters={"scenario": state["scenario"]},
            result_summary=f"Found {len(candidates)} candidate plans.",
            next_action="generate_script",
            rationale="Candidates are required before a script can be generated.",
            decision_source="rule",
        )
        return {
            "candidates": candidates,
            "tool_call_count": state["tool_call_count"] + 1,
            "next_route": "generate_script",
        }

    def generate_script(state: GraphState) -> dict:
        if limit_reached(state, "generate_script"):
            return {"next_route": "finish"}
        candidate = selected_candidate(state)
        _generate_script(audit_repository, state["result_object"], candidate)
        trace(
            state["result_object"],
            node="generate_script",
            action="generate_script",
            parameters={"candidate_id": candidate.candidate_id},
            result_summary="Generated a candidate script artifact.",
            next_action="estimate_cost",
            rationale="Cost estimation requires a generated script.",
            decision_source="rule",
        )
        return {
            "tool_call_count": state["tool_call_count"] + 1,
            "next_route": "estimate_cost",
        }

    def estimate_cost(state: GraphState) -> dict:
        if limit_reached(state, "estimate_cost"):
            return {"next_route": "finish"}
        candidate = selected_candidate(state)
        parameters = {
            "candidate_id": candidate.candidate_id,
            "attempt": state["estimate_attempt"],
        }
        if state.get("interrupt_before") == "estimate_cost":
            interrupt(
                {
                    "action": "resume_before_estimate_cost",
                    "candidate_id": candidate.candidate_id,
                    "message": "Execution paused before cost estimation.",
                }
            )
            trace(
                state["result_object"],
                node="estimate_cost",
                action="resume_execution",
                parameters={"candidate_id": candidate.candidate_id},
                result_summary="Execution resumed from the checkpoint before cost estimation.",
                next_action="estimate_cost",
                rationale="The previous successful script artifact is reused after resumption.",
                decision_source="rule",
            )
        if (
            state["scenario"] == "tool-failure"
            and state["estimate_attempt"] == 1
            and state.get("fail_tool") == "estimate_cost"
            and state.get("fail_on_attempt") == 1
        ):
            _record_estimate_failure(
                audit_repository,
                state["result_object"],
                candidate,
                attempt=state["estimate_attempt"],
            )
            trace(
                state["result_object"],
                node="estimate_cost",
                action="estimate_cost",
                parameters=parameters,
                result_summary="Cost estimator returned TOOL_UNAVAILABLE.",
                next_action="evaluate_constraints",
                rationale="The failure is retryable, so retry eligibility must be evaluated.",
                decision_source="rule",
            )
            return {
                "last_estimate_failed": True,
                "tool_call_count": state["tool_call_count"] + 1,
                "next_route": "evaluate_constraints",
            }
        _estimate_candidate(
            audit_repository,
            state["result_object"],
            candidate,
            attempt=state["estimate_attempt"],
        )
        trace(
            state["result_object"],
            node="estimate_cost",
            action="estimate_cost",
            parameters=parameters,
            result_summary=(
                f"Estimated cost={candidate.base_cost}, duration={candidate.duration_minutes} minutes."
            ),
            next_action="evaluate_constraints",
            rationale="The deterministic constraint guard now evaluates feasibility.",
            decision_source="rule",
        )
        return {
            "last_estimate_failed": False,
            "tool_call_count": state["tool_call_count"] + 1,
            "next_route": "evaluate_constraints",
        }

    def evaluate_constraints(state: GraphState) -> dict:
        result = state["result_object"]
        candidate = selected_candidate(state)
        if state["last_estimate_failed"]:
            result.events.append(
                {
                    "type": "retry",
                    "step_id": f"estimate_cost:{candidate.candidate_id}",
                    "reason": "TOOL_UNAVAILABLE",
                }
            )
            trace(
                result,
                node="evaluate_constraints",
                action="request_retry",
                parameters={"step_id": f"estimate_cost:{candidate.candidate_id}", "attempt": 2},
                result_summary="The cost estimator failed with a retryable error.",
                next_action="estimate_cost",
                rationale="The retry policy allows one additional estimate attempt.",
                decision_source="rule",
            )
            return {"next_route": "retry", "estimate_attempt": 2}

        reason = constraint_violation(state, candidate)
        if reason is None:
            trace(
                result,
                node="evaluate_constraints",
                action="validate_constraints",
                parameters={"candidate_id": candidate.candidate_id},
                result_summary="Candidate satisfies budget and deadline constraints.",
                next_action="save_plan",
                rationale="Only a feasible candidate may be saved.",
                decision_source="rule",
            )
            return {"next_route": "save"}
        if state["selected_index"] + 1 < len(state["candidates"]):
            trace(
                result,
                node="evaluate_constraints",
                action="reject_candidate",
                parameters={"candidate_id": candidate.candidate_id, "reason": reason},
                result_summary=f"Candidate violates {reason}.",
                next_action="decide_replan",
                rationale="An untried alternative exists and should be considered.",
                decision_source="rule",
            )
            return {
                "next_route": "replan",
                "estimate_attempt": 1,
                "replan_reason": reason,
            }

        result.status = RunStatus.PARTIAL
        minimum_cost = min(item.base_cost for item in state["candidates"])
        result.failure_reason = {
            "code": "NO_FEASIBLE_PLAN",
            "minimum_cost": str(minimum_cost),
            "budget_gap": str(max(0, minimum_cost - result.budget)),
        }
        trace(
            result,
            node="evaluate_constraints",
            action="declare_no_feasible_plan",
            parameters={"reason": reason},
            result_summary="No candidate satisfies the active constraints.",
            next_action="finalize",
            rationale="All candidates were exhausted without a safe save path.",
            decision_source="rule",
        )
        return {"next_route": "finish"}

    def decide_replan(state: GraphState) -> dict:
        result = state["result_object"]
        rejected = selected_candidate(state)
        alternatives = state["candidates"][state["selected_index"] + 1 :]
        replacement = select_replacement_with_llm(result, rejected, alternatives)
        if replacement is None:
            replacement = alternatives[0]
            source = "fallback" if any(
                event["type"] == "llm_fallback" for event in result.events
            ) else "rule"
            result.planner_mode = source
        else:
            source = "live_llm"
            result.planner_mode = "llm"
        audit_repository.record_replan(
            result,
            rejected_candidate_id=rejected.candidate_id,
            selected_candidate_id=replacement.candidate_id,
            reason=state["replan_reason"],
        )
        result.events.append(
            {
                "type": "replan",
                "reason": state["replan_reason"],
                "from_candidate_id": rejected.candidate_id,
                "to_candidate_id": replacement.candidate_id,
                "planner_mode": result.planner_mode,
            }
        )
        trace(
            result,
            node="decide_replan",
            action="select_candidate",
            parameters={
                "rejected_candidate_id": rejected.candidate_id,
                "selected_candidate_id": replacement.candidate_id,
            },
            result_summary="Selected an alternative candidate for replanning.",
            next_action="generate_script",
            rationale=state["replan_reason"],
            decision_source=source,
        )
        return {
            "selected_index": state["candidates"].index(replacement),
            "estimate_attempt": 1,
            "next_route": "generate_script",
        }

    def save_plan(state: GraphState) -> dict:
        if limit_reached(state, "save_plan"):
            return {"next_route": "finish"}
        candidate = selected_candidate(state)
        _complete_with_saved_plan(audit_repository, state["result_object"], candidate)
        trace(
            state["result_object"],
            node="save_plan",
            action="save_plan",
            parameters={"candidate_id": candidate.candidate_id},
            result_summary="Saved a budget-compliant content plan.",
            next_action="finalize",
            rationale="All dependencies and deterministic constraints succeeded.",
            decision_source="rule",
        )
        return {
            "tool_call_count": state["tool_call_count"] + 1,
            "next_route": "finalize",
        }

    def finalize(state: GraphState) -> dict:
        result = state["result_object"]
        audit_repository.update_run(result)
        trace(
            result,
            node="finalize",
            action="finalize_run",
            parameters={"status": result.status},
            result_summary=f"Run finalized with status={result.status}.",
            next_action="end",
            rationale="The workflow reached a terminal state.",
            decision_source="rule",
        )
        return {"result": result.to_dict()}

    def limit_reached(state: GraphState, action: str) -> bool:
        max_tool_calls = state.get("max_tool_calls", DEFAULT_MAX_TOOL_CALLS)
        if state["tool_call_count"] < max_tool_calls:
            return False
        result = state["result_object"]
        result.status = RunStatus.PARTIAL
        result.failure_reason = {
            "code": "EXECUTION_LIMIT_REACHED",
            "limit_type": "tool_calls",
            "limit": str(max_tool_calls),
        }
        trace(
            result,
            node="execution_guard",
            action=action,
        parameters={"tool_call_count": state["tool_call_count"], "limit": max_tool_calls},
            result_summary="Execution stopped before the tool-call limit was exceeded.",
            next_action="finalize",
            rationale="The agent must return incomplete rather than loop indefinitely.",
            decision_source="rule",
        )
        return True

    workflow = StateGraph(GraphState)
    workflow.add_node("initialize", initialize)
    workflow.add_node("search_assets", search_assets)
    workflow.add_node("generate_script", generate_script)
    workflow.add_node("estimate_cost", estimate_cost)
    workflow.add_node("evaluate_constraints", evaluate_constraints)
    workflow.add_node("decide_replan", decide_replan)
    workflow.add_node("save_plan", save_plan)
    workflow.add_node("finalize", finalize)
    workflow.add_edge(START, "initialize")
    workflow.add_conditional_edges(
        "initialize", route_after("search_assets"), {"search_assets": "search_assets", "finalize": "finalize"}
    )
    workflow.add_conditional_edges(
        "search_assets", route_after("generate_script"), {"generate_script": "generate_script", "finish": "finalize"}
    )
    workflow.add_conditional_edges(
        "generate_script", route_after("estimate_cost"), {"estimate_cost": "estimate_cost", "finish": "finalize"}
    )
    workflow.add_conditional_edges(
        "estimate_cost", route_after("evaluate_constraints"), {"evaluate_constraints": "evaluate_constraints", "finish": "finalize"}
    )
    workflow.add_conditional_edges(
        "evaluate_constraints",
        lambda state: state["next_route"],
        {"retry": "estimate_cost", "replan": "decide_replan", "save": "save_plan", "finish": "finalize"},
    )
    workflow.add_edge("decide_replan", "generate_script")
    workflow.add_conditional_edges(
        "save_plan", route_after("finalize"), {"finalize": "finalize", "finish": "finalize"}
    )
    workflow.add_edge("finalize", END)
    return workflow.compile(checkpointer=build_checkpointer(database_path))


def invoke_scenario(
    *,
    database_path: Path | str,
    scenario: str,
    thread_id: str,
    fail_tool: str | None = None,
    fail_on_attempt: int | None = None,
    interrupt_before: str | None = None,
    run_id: str | None = None,
    topic: str | None = None,
    budget: int | None = None,
    deadline: str | None = None,
    idempotency_key: str | None = None,
    max_tool_calls: int | None = None,
) -> dict:
    """Invoke a bounded workflow using ``thread_id`` for checkpoint persistence."""
    return build_workflow(database_path).invoke(
        {
            "scenario": scenario,
            "fail_tool": fail_tool,
            "fail_on_attempt": fail_on_attempt,
            "requested_run_id": run_id,
            "requested_topic": topic,
            "requested_budget": budget,
            "requested_deadline": deadline,
            "requested_idempotency_key": idempotency_key,
            "max_tool_calls": max_tool_calls or DEFAULT_MAX_TOOL_CALLS,
            "interrupt_before": interrupt_before,
        },
        config={"configurable": {"thread_id": thread_id}},
    )


def resume_scenario(*, database_path: Path | str, thread_id: str) -> dict:
    """Resume one interrupted LangGraph thread from its SQLite checkpoint."""
    return build_workflow(database_path).invoke(
        Command(
            resume={"action": "continue"},
            update={"interrupt_before": None},
        ),
        config={"configurable": {"thread_id": thread_id}},
    )


def route_after(default: str):
    def route(state: GraphState) -> str:
        return state.get("next_route", default)

    return route


def selected_candidate(state: GraphState) -> Candidate:
    return state["candidates"][state["selected_index"]]


def constraint_violation(state: GraphState, candidate: Candidate) -> str | None:
    if candidate.base_cost > state["result_object"].budget:
        return "BUDGET_EXCEEDED"
    if state["scenario"] == "deadline-replan" and candidate.duration_minutes > 60:
        return "DEADLINE_EXCEEDED"
    return None


def _candidates_for_scenario(scenario: str) -> list[Candidate]:
    scenarios = {
        "over-budget-replan": OVER_BUDGET_REPLAN_CANDIDATES,
        "tool-failure": TOOL_FAILURE_CANDIDATES,
        "no-feasible-plan": NO_FEASIBLE_CANDIDATES,
        "deadline-replan": DEADLINE_REPLAN_CANDIDATES,
    }
    try:
        return list(scenarios[scenario])
    except KeyError as error:
        raise ValueError(f"Unknown demo scenario: {scenario}") from error


def select_replacement_with_llm(
    result: PlanningResult,
    rejected: Candidate,
    alternatives: list[Candidate],
) -> Candidate | None:
    """Accept only an allowed LLM candidate selection; otherwise signal fallback."""
    model = build_decision_model(load_llm_config())
    if model is None:
        return None
    candidate_summary = [
        {
            "candidate_id": item.candidate_id,
            "cost": item.base_cost,
            "duration_minutes": item.duration_minutes,
        }
        for item in alternatives
    ]
    prompt = (
        "Choose exactly one replacement candidate using select_candidate. "
        f"Topic: {result.topic}. Budget: {result.budget}. "
        f"Rejected candidate: {rejected.candidate_id}. "
        f"Allowed alternatives: {candidate_summary}."
    )
    try:
        response = model.invoke([HumanMessage(content=prompt)])
    except Exception as error:
        result.events.append({"type": "llm_fallback", "reason": type(error).__name__})
        return None
    selected = extract_candidate_choice(
        response, {item.candidate_id for item in alternatives}
    )
    if selected is None:
        result.events.append({"type": "llm_fallback", "reason": "INVALID_LLM_ACTION"})
        return None
    selected_id, reason = selected
    result.events.append(
        {"type": "llm_decision", "candidate_id": selected_id, "reason": reason}
    )
    return next(item for item in alternatives if item.candidate_id == selected_id)
