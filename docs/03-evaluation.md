# 03 Evaluation

Run all tests from the question root:

```powershell
python -m pytest -v
```

The repository records deterministic evidence with:

```powershell
python scripts\record_examples.py
```

| Acceptance point | Evidence | Actual result |
|---|---|---|
| Budget 10 replans 12 to 8 and saves | [`examples/01-budget-replan.json`](../examples/01-budget-replan.json) | `completed`, `actual_cost=8`, one replan, saved plan present |
| Budget 7 cannot save and reports gap | [`examples/02-no-feasible-plan.json`](../examples/02-no-feasible-plan.json) | `partial`, no saved plan, minimum cost 8, gap 1 |
| Tool failure is not marked successful and is retried | [`examples/03-tool-failure-retry.json`](../examples/03-tool-failure-retry.json) | `estimate_cost` attempt 1 fails, attempt 2 succeeds, script remains single successful artifact |
| Live LLM selects an allowed alternative | [`examples/04-live-llm.json`](../examples/04-live-llm.json) | `decision_source=live_llm`, `planner_mode=llm`, safe trace persisted |

## Failure Behavior

- Invalid inputs return `blocked` before tool calls.
- LLM absence is `planner_mode: "rule"`; LLM errors are `planner_mode: "fallback"`.
- Tool-call limit returns `partial` with `EXECUTION_LIMIT_REACHED`.

## Known Limitations

- The evidence scenarios use synthetic local tools.
- A live LLM request has been executed and redacted evidence is committed in `examples/04-live-llm.json`.
- `resume` is idempotent for terminal runs and never repeats stored tool calls. The `demo --interrupt-before estimate_cost` scenario provides a controlled checkpoint boundary; resume preserves the generated script and continues from estimation.

## Live LLM Evaluation Procedure

After configuring `.env`, run:

```powershell
python scripts\record_live_llm_evidence.py
```

This writes `examples/04-live-llm.json` only after the model produces a valid constrained selection. The record includes `decision_source: "live_llm"` and deliberately excludes credentials, private gateway URLs, headers, and prompt bodies.
