from __future__ import annotations

import pytest

from scripts.record_live_llm_evidence import require_live_llm_config


def test_live_evaluation_requires_a_complete_gateway_configuration() -> None:
    with pytest.raises(RuntimeError, match="LLM_BASE_URL"):
        require_live_llm_config({})
