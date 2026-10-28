from __future__ import annotations

import json

from content_planner.cli import main


def test_demo_command_prints_auditable_json_result(tmp_path, capsys) -> None:
    exit_code = main(
        [
            "--database-path",
            str(tmp_path / "planner.db"),
            "demo",
            "--scenario",
            "over-budget-replan",
        ]
    )

    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "completed"
    assert payload["actual_cost"] == 8
    assert payload["saved_plan_id"]


def test_run_command_accepts_the_planning_request_arguments(tmp_path, capsys) -> None:
    exit_code = main(
        [
            "--database-path",
            str(tmp_path / "planner.db"),
            "run",
            "--topic",
            "夏季防晒新品活动",
            "--budget",
            "10",
            "--deadline",
            "2030-10-30T18:00:00+08:00",
        ]
    )

    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "completed"


def test_cli_warns_when_llm_configuration_is_missing(tmp_path, capsys, monkeypatch) -> None:
    for name in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL", "LLM_API_MODE"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr("content_planner.config.PROJECT_ROOT", tmp_path)

    exit_code = main(
        [
            "--database-path",
            str(tmp_path / "planner.db"),
            "demo",
            "--scenario",
            "over-budget-replan",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert json.loads(captured.out)["planner_mode"] == "rule"
    assert "未检测到完整 LLM 配置" in captured.err


def test_cli_warns_when_llm_request_falls_back(tmp_path, capsys, monkeypatch) -> None:
    from content_planner.graph import workflow

    class UnavailableDecisionModel:
        def invoke(self, _messages):
            raise ConnectionError("gateway unavailable")

    monkeypatch.setattr(
        workflow, "build_decision_model", lambda _config: UnavailableDecisionModel()
    )

    exit_code = main(
        [
            "--database-path",
            str(tmp_path / "planner.db"),
            "demo",
            "--scenario",
            "over-budget-replan",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert json.loads(captured.out)["planner_mode"] == "fallback"
    assert "LLM 调用失败" in captured.err
    assert "ConnectionError" in captured.err


def test_demo_interrupt_option_returns_a_running_run(tmp_path, capsys) -> None:
    exit_code = main(
        [
            "--database-path",
            str(tmp_path / "planner.db"),
            "demo",
            "--scenario",
            "over-budget-replan",
            "--interrupt-before",
            "estimate_cost",
        ]
    )

    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "running"
