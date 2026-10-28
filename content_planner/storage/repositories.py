"""Audit repository used by deterministic graph nodes."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from content_planner.models import PlanningResult
from content_planner.storage.database import connect, dump_json


class PlannerRepository:
    def __init__(self, database_path: Path | str) -> None:
        self.connection = connect(database_path)

    def create_run(self, result: PlanningResult) -> None:
        self.connection.execute(
            """
            INSERT INTO runs
                (run_id, idempotency_key, topic, budget, deadline, status, planner_mode)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result.run_id,
                result.idempotency_key,
                result.topic,
                result.budget,
                result.deadline,
                result.status,
                result.planner_mode,
            ),
        )
        self.connection.commit()

    def get_run_by_idempotency_key(self, idempotency_key: str) -> PlanningResult | None:
        row = self.connection.execute(
            "SELECT * FROM runs WHERE idempotency_key = ?", (idempotency_key,)
        ).fetchone()
        if row is None:
            return None
        return PlanningResult(
            run_id=row["run_id"],
            status=row["status"],
            topic=row["topic"],
            budget=row["budget"],
            deadline=row["deadline"],
            idempotency_key=row["idempotency_key"],
            selected_candidate_id=row["selected_candidate_id"],
            actual_cost=row["actual_cost"],
            saved_plan_id=row["saved_plan_id"],
            replan_count=row["replan_count"],
            failure_reason=(
                json.loads(row["failure_reason_json"])
                if row["failure_reason_json"]
                else None
            ),
            planner_mode=row["planner_mode"],
        )

    def get_run(self, run_id: str) -> PlanningResult | None:
        row = self.connection.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
        if row is None:
            return None
        result = PlanningResult(
            run_id=row["run_id"],
            status=row["status"],
            topic=row["topic"],
            budget=row["budget"],
            deadline=row["deadline"],
            idempotency_key=row["idempotency_key"],
            selected_candidate_id=row["selected_candidate_id"],
            actual_cost=row["actual_cost"],
            saved_plan_id=row["saved_plan_id"],
            replan_count=row["replan_count"],
            failure_reason=(
                json.loads(row["failure_reason_json"])
                if row["failure_reason_json"]
                else None
            ),
            planner_mode=row["planner_mode"],
        )
        step_rows = self.connection.execute(
            "SELECT step_id, step_type, status, dependency_json, output_json, error_json "
            "FROM steps WHERE run_id = ? ORDER BY rowid", (run_id,)
        )
        result.steps = [
            {
                "step_id": item["step_id"],
                "step_type": item["step_type"],
                "status": item["status"],
                "dependencies": json.loads(item["dependency_json"]),
                "output": json.loads(item["output_json"]) if item["output_json"] else None,
                "error": json.loads(item["error_json"]) if item["error_json"] else None,
            }
            for item in step_rows
        ]
        tool_rows = self.connection.execute(
            "SELECT step_id, tool_name, attempt, ok, result_json, error_json "
            "FROM tool_results WHERE run_id = ? ORDER BY id", (run_id,)
        )
        result.tool_results = [
            {
                "step_id": item["step_id"],
                "tool_name": item["tool_name"],
                "attempt": item["attempt"],
                "ok": bool(item["ok"]),
                "result": json.loads(item["result_json"]) if item["result_json"] else None,
                "error": json.loads(item["error_json"]) if item["error_json"] else None,
            }
            for item in tool_rows
        ]
        result.trace = [
            {
                "sequence": item["sequence"],
                "node": item["node"],
                "action": item["action"],
                "parameters": json.loads(item["parameters_json"]),
                "result_summary": item["result_summary"],
                "next_action": item["next_action"],
                "rationale": item["rationale"],
                "decision_source": item["decision_source"],
            }
            for item in self.connection.execute(
                "SELECT * FROM traces WHERE run_id = ? ORDER BY sequence", (run_id,)
            )
        ]
        return result

    def record_trace(
        self,
        result: PlanningResult,
        *,
        node: str,
        action: str,
        parameters: dict,
        result_summary: str,
        next_action: str,
        rationale: str,
        decision_source: str,
    ) -> None:
        entry = {
            "sequence": len(result.trace) + 1,
            "node": node,
            "action": action,
            "parameters": parameters,
            "result_summary": result_summary,
            "next_action": next_action,
            "rationale": rationale,
            "decision_source": decision_source,
        }
        result.trace.append(entry)
        self.connection.execute(
            """
            INSERT INTO traces
                (run_id, sequence, node, action, parameters_json, result_summary,
                 next_action, rationale, decision_source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result.run_id,
                entry["sequence"],
                entry["node"],
                entry["action"],
                dump_json(entry["parameters"]),
                entry["result_summary"],
                entry["next_action"],
                entry["rationale"],
                entry["decision_source"],
            ),
        )
        self.connection.commit()

    def list_runs_json(self) -> str:
        rows = self.connection.execute(
            "SELECT run_id, topic, budget, status, actual_cost, selected_candidate_id "
            "FROM runs ORDER BY rowid DESC"
        ).fetchall()
        return dump_json([dict(row) for row in rows])

    def record_step(
        self,
        result: PlanningResult,
        *,
        step_id: str,
        step_type: str,
        status: str,
        dependencies: list[str],
        output: dict | None = None,
        error: dict | None = None,
    ) -> None:
        step = {
            "step_id": step_id,
            "step_type": step_type,
            "status": status,
            "dependencies": dependencies,
            "output": output,
            "error": error,
        }
        result.steps.append(step)
        self.connection.execute(
            """
            INSERT OR REPLACE INTO steps
                (run_id, step_id, step_type, status, dependency_json, output_json, error_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result.run_id,
                step_id,
                step_type,
                status,
                dump_json(dependencies),
                dump_json(output) if output is not None else None,
                dump_json(error) if error is not None else None,
            ),
        )
        self.connection.commit()

    def record_tool_result(
        self,
        result: PlanningResult,
        *,
        step_id: str,
        tool_name: str,
        attempt: int,
        ok: bool,
        payload: dict | None = None,
        error: dict | None = None,
    ) -> None:
        item = {
            "step_id": step_id,
            "tool_name": tool_name,
            "attempt": attempt,
            "ok": ok,
            "result": payload,
            "error": error,
        }
        result.tool_results.append(item)
        self.connection.execute(
            """
            INSERT INTO tool_results
                (run_id, step_id, tool_name, attempt, ok, result_json, error_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result.run_id,
                step_id,
                tool_name,
                attempt,
                int(ok),
                dump_json(payload) if payload is not None else None,
                dump_json(error) if error is not None else None,
            ),
        )
        self.connection.commit()

    def record_replan(
        self,
        result: PlanningResult,
        *,
        rejected_candidate_id: str,
        selected_candidate_id: str | None,
        reason: str,
    ) -> None:
        result.replan_count += 1
        result.rejected_candidate_ids.append(rejected_candidate_id)
        self.connection.execute(
            """
            INSERT INTO replans (run_id, rejected_candidate_id, selected_candidate_id, reason)
            VALUES (?, ?, ?, ?)
            """,
            (result.run_id, rejected_candidate_id, selected_candidate_id, reason),
        )
        self.connection.commit()

    def update_run(self, result: PlanningResult) -> None:
        self.connection.execute(
            """
            UPDATE runs
            SET status = ?, actual_cost = ?, selected_candidate_id = ?, saved_plan_id = ?,
                replan_count = ?, failure_reason_json = ?
            WHERE run_id = ?
            """,
            (
                result.status,
                result.actual_cost,
                result.selected_candidate_id,
                result.saved_plan_id,
                result.replan_count,
                dump_json(result.failure_reason) if result.failure_reason else None,
                result.run_id,
            ),
        )
        self.connection.commit()

    def save_plan(self, result: PlanningResult, content: dict) -> str:
        plan_id = f"plan_{uuid4().hex[:12]}"
        self.connection.execute(
            """
            INSERT INTO saved_plans
                (plan_id, run_id, content_json, total_cost, estimated_duration_minutes)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                plan_id,
                result.run_id,
                dump_json(content),
                result.actual_cost,
                result.estimated_duration_minutes,
            ),
        )
        self.connection.commit()
        return plan_id
