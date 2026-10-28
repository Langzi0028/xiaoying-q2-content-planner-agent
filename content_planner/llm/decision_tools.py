"""Restricted LLM decision tools and defensive tool-call parsing."""

from __future__ import annotations

from langchain_core.messages import AIMessage
from langchain_core.tools import tool


@tool
def select_candidate(candidate_id: str, reason: str) -> str:
    """Select one candidate ID from the candidates supplied in the prompt."""
    return f"Candidate selection recorded for {candidate_id}: {reason}"


def extract_candidate_choice(
    response: AIMessage, allowed_candidate_ids: set[str]
) -> tuple[str, str] | None:
    """Accept only a valid, explicitly allowed candidate-selection tool call."""
    for tool_call in response.tool_calls:
        if tool_call["name"] != "select_candidate":
            continue
        candidate_id = tool_call["args"].get("candidate_id")
        reason = tool_call["args"].get("reason")
        if candidate_id in allowed_candidate_ids and isinstance(reason, str) and reason:
            return candidate_id, reason
    return None
