from __future__ import annotations

from langchain_core.messages import AIMessage

from content_planner.llm.decision_tools import extract_candidate_choice


def test_extract_candidate_choice_accepts_an_allowed_tool_call() -> None:
    response = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "select_candidate",
                "args": {
                    "candidate_id": "candidate_low_cost",
                    "reason": "预算可控",
                },
                "id": "call-1",
            }
        ],
    )

    choice = extract_candidate_choice(response, {"candidate_low_cost"})

    assert choice == ("candidate_low_cost", "预算可控")


def test_extract_candidate_choice_rejects_unavailable_candidate() -> None:
    response = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "select_candidate",
                "args": {"candidate_id": "invented", "reason": "不存在"},
                "id": "call-2",
            }
        ],
    )

    assert extract_candidate_choice(response, {"candidate_low_cost"}) is None
