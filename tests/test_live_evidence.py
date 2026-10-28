from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_live_llm_evidence_is_safely_redacted_when_present() -> None:
    evidence_path = PROJECT_ROOT / "examples" / "04-live-llm.json"
    if not evidence_path.exists():
        return

    text = evidence_path.read_text(encoding="utf-8").lower()
    evidence = json.loads(text)

    assert evidence["decision_source"] == "live_llm"
    assert evidence["actual_output"]["planner_mode"] == "llm"
    assert "authorization" not in text
    assert "bearer " not in text
    assert "http://" not in text
    assert "https://" not in text
