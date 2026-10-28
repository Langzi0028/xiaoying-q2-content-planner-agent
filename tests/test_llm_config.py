from __future__ import annotations

import pytest

from content_planner.config import LLMConfig, load_llm_config


def test_missing_llm_configuration_returns_fallback_mode() -> None:
    config = load_llm_config({})

    assert config.is_configured is False
    assert config.mode == "fallback"


def test_invalid_llm_api_mode_is_rejected() -> None:
    with pytest.raises(ValueError, match="LLM_API_MODE"):
        LLMConfig(
            base_url="https://proxy.example/v1",
            api_key="secret",
            model="test-model",
            api_mode="unsupported",
        )
