"""Record one safe live-LLM decision proof after configuring a gateway."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from content_planner.config import load_llm_config
from content_planner.service import run_demo


REQUIRED_KEYS = ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL")


def require_live_llm_config(environ: dict[str, str]) -> None:
    """Fail before any request when the live evaluation cannot be meaningful."""
    missing = [name for name in REQUIRED_KEYS if not environ.get(name)]
    if missing:
        raise RuntimeError("Live evaluation requires: " + ", ".join(missing))


def main() -> None:
    config = load_llm_config()
    try:
        require_live_llm_config(
            {
                "LLM_BASE_URL": config.base_url or "",
                "LLM_API_KEY": config.api_key or "",
                "LLM_MODEL": config.model or "",
            }
        )
    except RuntimeError as error:
        print(f"[提示] {error}", file=sys.stderr)
        raise SystemExit(2) from None
    runtime_dir = PROJECT_ROOT / "data" / "live-evaluation"
    database_path = runtime_dir / "live-llm.db"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    try:
        result = run_demo(database_path=database_path, scenario="over-budget-replan")
        if result.planner_mode != "llm":
            print(
                "[提示] Live evaluation did not receive a valid LLM decision; "
                f"planner_mode={result.planner_mode}",
                file=sys.stderr,
            )
            raise SystemExit(2)
        evidence = {
            "decision_source": "live_llm",
            "model": config.model,
            "api_mode": config.api_mode,
            "actual_output": result.to_dict(),
            "safety_note": (
                "The evidence intentionally excludes LLM_API_KEY, gateway URL, request headers, "
                "and prompt body."
            ),
        }
        output_path = PROJECT_ROOT / "examples" / "04-live-llm.json"
        output_path.write_text(
            json.dumps(evidence, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(output_path.relative_to(PROJECT_ROOT))
    finally:
        shutil.rmtree(runtime_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
