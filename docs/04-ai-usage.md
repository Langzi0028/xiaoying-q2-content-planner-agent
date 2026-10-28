# 04 AI Usage

AI assisted with initial code scaffolding, test generation, documentation drafting, and review checklists. The implementation was manually reviewed and changed to add deterministic constraint guards, SQLite persistence, trace records, execution limits, fallback notices, and direct `main.py` startup.

Claims supported by automated tests:

- Budget/deadline replanning, tool-failure retry, idempotency, traces, execution limits, CLI notices, and persistence are covered by `tests/`.
- Actual deterministic outputs and traces are committed under `examples/`.

Claims not made:

- No claim is made that a real model was contacted or that live model quality was evaluated. That claim requires a configured online gateway and a fresh safe evidence record.
