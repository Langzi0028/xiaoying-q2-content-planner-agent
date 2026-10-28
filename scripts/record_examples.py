"""Create safe, reproducible assessment evidence from deterministic scenarios."""

from __future__ import annotations

import json
import shutil
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from content_planner.service import run_demo, run_request


EXAMPLES_DIR = PROJECT_ROOT / "examples"
RUNTIME_DIR = PROJECT_ROOT / "data" / "example-runs"


def main() -> None:
    shutil.rmtree(RUNTIME_DIR, ignore_errors=True)
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    EXAMPLES_DIR.mkdir(exist_ok=True)

    cases = [
        (
            "01-budget-replan",
            "预算 10；初始候选成本 12；应重规划到成本 8。",
            "python main.py --database-path data/example-runs/01-budget-replan.db "
            'run --topic "夏季防晒新品活动" --budget 10 '
            '--deadline "2030-10-30T18:00:00+08:00"',
            lambda database_path: run_request(
                database_path=database_path,
                topic="夏季防晒新品活动",
                budget=10,
                deadline="2030-10-30T18:00:00+08:00",
            ),
        ),
        (
            "02-no-feasible-plan",
            "预算 7；所有候选均超预算；不允许保存方案。",
            "python main.py --database-path data/example-runs/02-no-feasible-plan.db "
            'run --topic "低预算活动测试" --budget 7 '
            '--deadline "2030-10-30T18:00:00+08:00"',
            lambda database_path: run_request(
                database_path=database_path,
                topic="低预算活动测试",
                budget=7,
                deadline="2030-10-30T18:00:00+08:00",
            ),
        ),
        (
            "03-tool-failure-retry",
            "第一次 estimate_cost 注入 TOOL_UNAVAILABLE；保留脚本并重试一次。",
            "python main.py --database-path data/example-runs/03-tool-failure-retry.db "
            "demo --scenario tool-failure --fail-tool estimate_cost --fail-on-attempt 1",
            lambda database_path: run_demo(
                database_path=database_path,
                scenario="tool-failure",
                fail_tool="estimate_cost",
                fail_on_attempt=1,
            ),
        ),
    ]

    for name, description, command, execute in cases:
        database_path = RUNTIME_DIR / f"{name}.db"
        result = execute(database_path)
        evidence = {
            "description": description,
            "command": command,
            "actual_output": result.to_dict(),
            "database_rows": _database_rows(database_path),
            "verification": _verification(result.to_dict()),
        }
        output_path = EXAMPLES_DIR / f"{name}.json"
        output_path.write_text(
            json.dumps(evidence, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(output_path.relative_to(PROJECT_ROOT))

    shutil.rmtree(RUNTIME_DIR, ignore_errors=True)
    _write_index()


def _write_index() -> None:
    lines = ["# Assessment Evidence", ""]
    for file in sorted(EXAMPLES_DIR.glob("0[1-3]-*.json")):
        evidence = json.loads(file.read_text(encoding="utf-8"))
        result = evidence["actual_output"]
        lines.extend(
            [
                f"## {file.stem}",
                "",
                f"- Input: `{evidence['command']}`",
                f"- Actual status: `{result['status']}`",
                f"- Planner mode: `{result['planner_mode']}`",
                f"- Trace entries: `{len(result['trace'])}`",
                f"- Database rows: `{evidence['database_rows']}`",
                "",
            ]
        )
    (EXAMPLES_DIR / "README.md").write_text(
        "\n".join(lines), encoding="utf-8-sig"
    )


def _database_rows(database_path: Path) -> dict[str, int]:
    connection = sqlite3.connect(database_path)
    tables = ("runs", "steps", "tool_results", "replans", "saved_plans", "traces")
    counts = {
        table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in tables
    }
    connection.close()
    return counts


def _verification(result: dict) -> dict[str, object]:
    return {
        "status": result["status"],
        "planner_mode": result["planner_mode"],
        "replan_count": result["replan_count"],
        "saved_plan_id_present": bool(result["saved_plan_id"]),
        "trace_entries": len(result["trace"]),
        "failed_tool_attempts": [
            item
            for item in result["tool_results"]
            if item["ok"] is False
        ],
    }


if __name__ == "__main__":
    main()
