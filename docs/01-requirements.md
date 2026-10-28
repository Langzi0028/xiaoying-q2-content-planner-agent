# 01 Requirements

## User And Goal

An operations specialist enters an activity topic, budget, and deadline. The agent must create and save a feasible content plan, or return an auditable unfinished reason.

## Scope

- Local Python CLI started with `python main.py`.
- Synthetic asset retrieval, script generation, cost estimation, and plan-saving tools.
- LangGraph orchestration, SQLite audit/checkpoints, optional OpenAI-compatible LLM decision adapter.
- Budget/deadline replanning, retryable tool failure handling, idempotency, and run inspection/resume.

## Non-goals

- Production asset provider, real publishing, external database, web UI, or credential storage.
- Claiming real LLM quality without an actual configured online request.

## Success Criteria

- Budget 10 rejects estimated cost 12 and saves the cost-8 alternative.
- Missing required fields make zero tool calls.
- Retryable cost-tool failure remains failed in audit data, preserves successful script data, then retries once.
- No feasible plan is not saved and reports the minimum budget gap.
- Every run persists steps, tool results, trace, replans, and final state in SQLite.

## Known Constraints

- Without complete `.env` gateway configuration, the deterministic rule planner is used and labeled `planner_mode: "rule"`.
- A configured but failing model falls back safely and is labeled `planner_mode: "fallback"`.
- Live LLM evidence requires a user-provided reachable gateway and is not included until one is configured.
