"""LangGraph checkpoint construction backed by the planner SQLite database."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver


def build_checkpointer(database_path: Path | str) -> SqliteSaver:
    """Return a LangGraph saver using the same local SQLite file as audit data."""
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, check_same_thread=False)
    return SqliteSaver(connection)
