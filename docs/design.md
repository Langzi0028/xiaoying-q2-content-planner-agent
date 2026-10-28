# Content Task Planning Agent Design

## Goal

This command-line agent helps an operator complete a content activity plan within a budget and deadline. It keeps auditable step state, actual tool results, accumulated costs, replanning events, and either a saved plan or an explicit unfinished reason.

## Contract Boundaries

- CLI commands are local only and start through `python main.py`; no HTTP API or remote database contract is introduced.
- `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`, and `LLM_API_MODE` configure an OpenAI-compatible gateway. A project-root `.env` is automatically loaded with shell/PyCharm values taking precedence. Secrets are never printed or stored.
- Runtime state is stored in `data/content_planner.db`, which is excluded from Git.
- The local simulator provides deterministic assets, script generation, cost estimation, and plan saving for repeatable assessment tests.

## Workflow

`run` validates inputs, then invokes a LangGraph `StateGraph` with a checkpoint stored in the same SQLite file as the business audit tables. The graph explicitly traverses asset search, script generation, cost estimation, constraint evaluation, retry/replan, save, and finalization nodes.

When a model gateway is configured, the replan node calls LangChain `ChatOpenAI` and binds only `select_candidate`. The program validates that the returned candidate is one of the allowed alternatives before changing graph state. A missing, failed, or malformed LLM response uses the deterministic alternative and records `planner_mode: "rule"` or `"fallback"`; tool costs, status, and saving remain entirely program-controlled.

The CLI keeps final JSON on stdout. It writes a concise stderr notice when LLM configuration is missing or when a configured LLM request falls back; notices contain only the failure type and never include credentials.

## Persistence

- `runs`: overall request status, selected candidate, actual cost, saved plan ID, failure reason.
- `steps`: step state, dependencies, output, and error.
- `tool_results`: every attempt and tool result; failed attempts remain failed.
- `replans`: rejected candidate, replacement candidate, and reason.
- `saved_plans`: only plans that passed deterministic constraints.
- LangGraph creates its checkpoint tables in this same database, keyed by `thread_id`.

## Deterministic Safety Rules

- Invalid topic, budget, or deadline returns `blocked` before tools run.
- A plan cannot be saved if its actual cost exceeds the budget.
- Failed tool attempts are persisted as `failed`; they are never converted into successes.
- A retry keeps earlier successful artifacts; it does not repeat successful script generation.
- The `over-budget-replan` scenario estimates cost `12` first, then rejects it and selects cost `8` under a budget of `10`.
- The `no-feasible-plan` scenario never writes `saved_plans` and returns the minimum budget gap.
- The `deadline-replan` scenario rejects a 120-minute candidate for a 30-minute alternative.

## Trace And Execution Limit

Every run persists an ordered `trace` list with node/action, safe parameters, result summary, next action, rationale, and decision source. The graph allows at most 12 tool calls by default; exhaustion returns `partial` with `EXECUTION_LIMIT_REACHED`.

## Known Scope Limit

`resume` returns terminal runs without duplicate calls and can continue the controlled `--interrupt-before estimate_cost` boundary without replaying the generated script. A configured gateway has completed one constrained live model selection; the redacted proof is `examples/04-live-llm.json`.
