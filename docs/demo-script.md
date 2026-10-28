# Assessment Demo Script

Run from the project root after installing dependencies with `python -m pip install -r requirements.txt`.

```powershell
# 1. Required reference case: budget 10, initial estimate 12, fallback estimate 8.
python main.py demo --scenario over-budget-replan

# 2. Inject one retryable cost-estimator failure. The script artifact remains successful.
python main.py demo --scenario tool-failure --fail-tool estimate_cost --fail-on-attempt 1

# 3. All candidates exceed budget. No plan is saved and the budget gap is shown.
python main.py demo --scenario no-feasible-plan

# 4. A deadline violation chooses the shorter alternative.
python main.py demo --scenario deadline-replan

# 5. Normal request route: it validates input, invokes LangGraph, and creates a checkpoint.
python main.py run --topic "夏季防晒新品活动" --budget 10 --deadline "2030-10-30T18:00:00+08:00"

# 6. Run the full regression suite.
python -m pytest -v

# 7. Regenerate the three committed actual-output/trace evidence files.
python scripts\record_examples.py

# 8. Bonus: pause before estimation and resume without replaying the generated script.
python main.py --database-path data\resume-demo.db demo --scenario over-budget-replan --interrupt-before estimate_cost
# Copy the returned run_id, then:
python main.py --database-path data\resume-demo.db resume --run-id <run_id>
```

Review the JSON output: the `steps`, `tool_results`, `rejected_candidate_ids`, `replan_count`, `actual_cost`, and `saved_plan_id` fields provide the evidence required by the assessment.
