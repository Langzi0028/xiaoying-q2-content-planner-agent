"""SQLite schema and connection helpers."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    idempotency_key TEXT UNIQUE,
    topic TEXT NOT NULL,
    budget INTEGER NOT NULL,
    deadline TEXT NOT NULL,
    status TEXT NOT NULL,
    actual_cost INTEGER NOT NULL DEFAULT 0,
    selected_candidate_id TEXT,
    saved_plan_id TEXT,
    replan_count INTEGER NOT NULL DEFAULT 0,
    planner_mode TEXT NOT NULL,
    failure_reason_json TEXT
);
CREATE TABLE IF NOT EXISTS steps (
    run_id TEXT NOT NULL,
    step_id TEXT NOT NULL,
    step_type TEXT NOT NULL,
    status TEXT NOT NULL,
    dependency_json TEXT NOT NULL,
    input_json TEXT,
    output_json TEXT,
    error_json TEXT,
    PRIMARY KEY (run_id, step_id)
);
CREATE TABLE IF NOT EXISTS tool_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    step_id TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    attempt INTEGER NOT NULL,
    ok INTEGER NOT NULL,
    result_json TEXT,
    error_json TEXT
);
CREATE TABLE IF NOT EXISTS replans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    rejected_candidate_id TEXT NOT NULL,
    selected_candidate_id TEXT,
    reason TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS saved_plans (
    plan_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL UNIQUE,
    content_json TEXT NOT NULL,
    total_cost INTEGER NOT NULL,
    estimated_duration_minutes INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS traces (
    run_id TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    node TEXT NOT NULL,
    action TEXT NOT NULL,
    parameters_json TEXT NOT NULL,
    result_summary TEXT NOT NULL,
    next_action TEXT NOT NULL,
    rationale TEXT NOT NULL,
    decision_source TEXT NOT NULL,
    PRIMARY KEY (run_id, sequence)
);
"""


def connect(database_path: Path | str) -> sqlite3.Connection:
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA)
    return connection


def dump_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)
