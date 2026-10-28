# 04 AI Usage

AI assisted with initial code scaffolding, test generation, documentation drafting, and review checklists. The implementation was manually reviewed and changed to add deterministic constraint guards, SQLite persistence, trace records, execution limits, fallback notices, and direct `main.py` startup.

Claims supported by automated tests:

- Budget/deadline replanning, tool-failure retry, idempotency, traces, execution limits, CLI notices, and persistence are covered by `tests/`.
- Actual deterministic outputs and traces are committed under `examples/`.

Live-model evidence:

- A configured online model made a constrained alternative-selection decision. Safe proof is committed in `examples/04-live-llm.json` with `decision_source: "live_llm"`.
- The record intentionally excludes the API key, gateway URL, headers, and prompt body; it proves only the bounded model decision path, not broad model quality.
