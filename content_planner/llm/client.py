"""Create an OpenAI-compatible LangChain chat client when configured."""

from __future__ import annotations

from langchain_openai import ChatOpenAI

from content_planner.config import LLMConfig
from content_planner.llm.decision_tools import select_candidate


def build_chat_model(config: LLMConfig) -> ChatOpenAI | None:
    """Build a model client without invoking it or exposing its credential."""
    if not config.is_configured:
        return None
    return ChatOpenAI(
        model=config.model,
        api_key=config.api_key,
        base_url=config.base_url,
        use_responses_api=config.api_mode == "responses",
    )


def build_decision_model(config: LLMConfig):
    """Bind only constrained planning decisions; business tools stay local."""
    model = build_chat_model(config)
    return model.bind_tools([select_candidate]) if model else None
