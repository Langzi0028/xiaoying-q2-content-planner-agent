from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_assessment_required_materials_are_present() -> None:
    required_paths = [
        "examples/01-budget-replan.json",
        "examples/02-no-feasible-plan.json",
        "examples/03-tool-failure-retry.json",
        "docs/01-requirements.md",
        "docs/02-solution.md",
        "docs/03-evaluation.md",
        "docs/04-ai-usage.md",
        "docs/05-retrospective.md",
    ]

    assert all((PROJECT_ROOT / path).is_file() for path in required_paths)
