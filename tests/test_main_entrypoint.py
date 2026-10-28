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


def test_main_entrypoint_loads_the_application_from_src_layout() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; from pathlib import Path; "
                "sys.path.insert(0, str(Path('src').resolve())); "
                "import content_planner; print(content_planner.__file__)"
            ),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        check=False,
        text=True,
    )

    assert completed.returncode == 0
    assert "src" in completed.stdout
    assert "content_planner" in completed.stdout
