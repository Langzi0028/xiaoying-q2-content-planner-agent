# 02 Solution

## Workflow

```text
initialize
-> search_assets
-> generate_script
-> estimate_cost
-> evaluate_constraints
   -> retry estimate_cost
   -> decide_replan -> generate_script
   -> save_plan
   -> finalize partial
-> finalize
```

## Dynamic Decisions

- `evaluate_constraints` rejects costs above budget or a deadline-violating candidate.
- `decide_replan` gives a configured LLM a constrained `select_candidate` tool; the selected ID must be in the program-supplied alternatives.
- Missing/invalid/failed LLM calls fall back to the first valid deterministic alternative.
- Retryable `TOOL_UNAVAILABLE` triggers one further cost-estimation attempt without repeating script generation.

## Framework And Version Boundaries

- LangGraph `<1.0` provides the explicit `StateGraph` and SQLite checkpointing.
- LangChain `<1.0` plus `langchain-openai` provides the optional OpenAI-compatible model client.
- `python-dotenv` loads an optional root `.env`; shell/PyCharm variables take precedence.

## Component Responsibilities

- `main.py`: direct executable entry point.
- `content_planner/cli.py`: argument parsing, stdout JSON, stderr notices.
- `graph/workflow.py`: bounded state graph, constraint guards, dynamic replan selection.
- `storage/`: business audit tables and LangGraph checkpoints in the same SQLite file.
- `llm/`: constrained model decision tool only; it cannot save plans or mutate cost/state.

## Safety And Limits

- A plan is saved only after deterministic budget/dependency checks.
- Trace records contain safe IDs/counts/reasons, never credentials or chain-of-thought.
- Default limit is 12 tool calls. Limit exhaustion returns `partial` with `EXECUTION_LIMIT_REACHED`.
- Machine-readable JSON is stdout; notices are stderr.
