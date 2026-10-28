from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_root_main_file_is_the_cli_entrypoint() -> None:
    completed = subprocess.run(
        [sys.executable, "main.py", "--help"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        check=False,
        text=True,
    )

    assert completed.returncode == 0
    assert "usage: python main.py" in completed.stdout
