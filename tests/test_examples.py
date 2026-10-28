from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_example_generator_creates_three_safe_trace_evidence_sets() -> None:
    subprocess.run(
        [sys.executable, "scripts/record_examples.py"],
        cwd=PROJECT_ROOT,
        check=True,
    )

    files = sorted((PROJECT_ROOT / "examples").glob("*.json"))

    assert [file.name for file in files] == [
        "01-budget-replan.json",
        "02-no-feasible-plan.json",
        "03-tool-failure-retry.json",
    ]
    for file in files:
        evidence = json.loads(file.read_text(encoding="utf-8"))
        assert evidence["actual_output"]["trace"]
        assert evidence["database_rows"]["traces"] > 0
    assert "Assessment Evidence" in (PROJECT_ROOT / "examples" / "README.md").read_text(
        encoding="utf-8"
    )
