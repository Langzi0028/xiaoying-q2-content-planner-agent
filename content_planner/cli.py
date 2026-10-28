"""Command-line interface for assessment demonstrations."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from content_planner.presentation import render_json
from content_planner.service import load_run, resume_run, run_demo, run_request


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python main.py")
    parser.add_argument(
        "--database-path",
        default="data/content_planner.db",
        help="SQLite database location (default: data/content_planner.db)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo = subparsers.add_parser("demo", help="Run a deterministic assessment scenario")
    demo.add_argument(
        "--scenario",
        required=True,
        choices=[
            "over-budget-replan",
            "tool-failure",
            "no-feasible-plan",
            "deadline-replan",
        ],
    )
    demo.add_argument("--fail-tool")
    demo.add_argument("--fail-on-attempt", type=int)
    demo.add_argument(
        "--interrupt-before",
        choices=["estimate_cost"],
        help="Pause a run before the named node so it can be resumed.",
    )
    run = subparsers.add_parser("run", help="Validate and run a planning request")
    run.add_argument("--topic", required=True)
    run.add_argument("--budget", required=True, type=int)
    run.add_argument("--deadline", required=True)
    run.add_argument("--idempotency-key")
    show = subparsers.add_parser("show", help="Show a persisted run and audit trail")
    show.add_argument("--run-id", required=True)
    resume = subparsers.add_parser("resume", help="Resume an unfinished run")
    resume.add_argument("--run-id", required=True)
    subparsers.add_parser("list-runs", help="List persisted runs")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "demo":
        result = run_demo(
            database_path=Path(args.database_path),
            scenario=args.scenario,
            fail_tool=args.fail_tool,
            fail_on_attempt=args.fail_on_attempt,
            interrupt_before=args.interrupt_before,
        )
        _print_llm_notice(result)
        print(render_json(result))
        return 0
    if args.command == "run":
        result = run_request(
            database_path=Path(args.database_path),
            topic=args.topic,
            budget=args.budget,
            deadline=args.deadline,
            idempotency_key=args.idempotency_key,
        )
        _print_llm_notice(result)
        print(render_json(result))
        return 0 if result.status == "completed" else 2
    if args.command == "show":
        result = load_run(database_path=Path(args.database_path), run_id=args.run_id)
        if result is None:
            print('{"error":"RUN_NOT_FOUND"}')
            return 2
        print(render_json(result))
        return 0
    if args.command == "resume":
        try:
            result = resume_run(
                database_path=Path(args.database_path),
                run_id=args.run_id,
            )
        except ValueError as error:
            print(render_json({"error": str(error)}))
            return 2
        _print_llm_notice(result)
        print(render_json(result))
        return 0 if result.status == "completed" else 2
    if args.command == "list-runs":
        from content_planner.storage.repositories import PlannerRepository

        repository = PlannerRepository(Path(args.database_path))
        print(repository.list_runs_json())
        return 0
    raise AssertionError(f"Unhandled command: {args.command}")


def _print_llm_notice(result) -> None:
    """Keep machine-readable output on stdout and runtime guidance on stderr."""
    if result.planner_mode == "rule":
        print(
            "[提示] 未检测到完整 LLM 配置，当前使用规则规划器；本次不会调用真实 LLM。",
            file=sys.stderr,
        )
        return
    if result.planner_mode == "fallback":
        reason = next(
            (
                event.get("reason", "未知原因")
                for event in result.events
                if event.get("type") == "llm_fallback"
            ),
            "未知原因",
        )
        print(
            f"[提示] LLM 调用失败（{reason}），已自动切换到规则规划器继续执行。",
            file=sys.stderr,
        )
