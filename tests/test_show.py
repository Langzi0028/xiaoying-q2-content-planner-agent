from __future__ import annotations

import json

from content_planner.cli import main
from content_planner.service import run_demo


def test_show_command_reads_a_saved_run_without_rerunning_tools(tmp_path, capsys) -> None:
    database_path = tmp_path / "planner.db"
    created = run_demo(database_path=database_path, scenario="over-budget-replan")

    exit_code = main(
        ["--database-path", str(database_path), "show", "--run-id", created.run_id]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["run_id"] == created.run_id
    assert payload["status"] == "completed"
    assert payload["steps"][0]["dependencies"] == []
    assert payload["tool_results"][0]["ok"] is True
