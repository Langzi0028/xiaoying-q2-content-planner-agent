from __future__ import annotations

from content_planner.graph.workflow import build_workflow


def test_langgraph_workflow_completes_budget_replan(tmp_path) -> None:
    graph = build_workflow(tmp_path / "planner.db")

    final_state = graph.invoke(
        {
            "scenario": "over-budget-replan",
            "fail_tool": None,
            "fail_on_attempt": None,
        },
        config={"configurable": {"thread_id": "test-over-budget"}},
    )

    assert final_state["result"]["status"] == "completed"
    assert final_state["result"]["selected_candidate_id"] == "candidate_low_cost"
    assert final_state["result"]["actual_cost"] == 8
