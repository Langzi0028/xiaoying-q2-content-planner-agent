"""Direct command-line entry point for the content planning agent."""

from __future__ import annotations

import sys
from pathlib import Path

# The source tree is intentionally explicit so reviewers can run this file directly.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from content_planner.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
