from __future__ import annotations

from content_planner.config import LLMConfig
from content_planner.llm.client import build_chat_model


def test_responses_mode_builds_langchain_chat_openai_client() -> None:
    client = build_chat_model(
        LLMConfig(
            base_url="https://proxy.example/v1",
            api_key="test-key",
            model="test-model",
            api_mode="responses",
        )
    )

    assert client is not None


def test_missing_gateway_configuration_returns_none() -> None:
    client = build_chat_model(
        LLMConfig(base_url=None, api_key=None, model=None, api_mode="fallback")
    )

    assert client is None
