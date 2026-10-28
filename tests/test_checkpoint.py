from __future__ import annotations

from content_planner.storage.checkpoints import build_checkpointer


def test_checkpointer_uses_the_shared_sqlite_database(tmp_path) -> None:
    database_path = tmp_path / "planner.db"

    checkpointer = build_checkpointer(database_path)

    assert checkpointer is not None
    assert database_path.exists()
