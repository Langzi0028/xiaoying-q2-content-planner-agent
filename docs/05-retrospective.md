# 05 Retrospective

## Hardest Issue

The main design challenge was separating model suggestions from authoritative state transitions. The final design lets the model choose only among validated candidate IDs while deterministic graph nodes own costs, step status, saving, and failure handling.

## Learning Outcomes

- A serial tool chain is not an agent: traceable observation and a changed next action are required.
- A failed tool result must remain failed even if later recovery succeeds.
- stdout/stderr separation keeps automated evaluation reliable while still giving operators useful notices.

## Actual Time And Scope

- Development occurred interactively during this assessment session; exact wall-clock duration was not tracked.
- Core deterministic loop, evidence, tests, and documentation are complete.

## Unfinished Work And Risks

- Live LLM online evaluation remains pending a reachable configured gateway.
- Mid-run interruption/resume needs an explicit interruption trigger for fuller demonstration.
- Local tool fixtures are intentionally synthetic and do not replace production integrations.

## Next Steps

1. Configure a gateway, run a live selection, and add safe `decision_source: "live_llm"` evidence.
2. Add a controlled interrupt before estimation, then demonstrate `resume` from checkpoint.
3. Create a Git commit and push the exact tested state before final submission.
