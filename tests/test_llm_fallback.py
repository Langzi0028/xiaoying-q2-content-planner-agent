from __future__ import annotations

from content_planner.graph import workflow
from content_planner.service import run_demo


class _UnavailableDecisionModel:
    def invoke(self, _messages):
        raise ConnectionError("gateway unavailable")


def test_llm_gateway_failure_falls_back_without_losing_replan(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        workflow, "build_decision_model", lambda _config: _UnavailableDecisionModel()
    )
    result = run_demo(
        database_path=tmp_path / "planner.db", scenario="over-budget-replan"
    )

    assert result.status == "completed"
    assert result.selected_candidate_id == "candidate_low_cost"
    assert result.planner_mode == "fallback"
    assert result.events[0]["type"] == "llm_fallback"
