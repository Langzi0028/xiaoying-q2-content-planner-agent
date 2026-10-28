# Assessment Evidence

## 01-budget-replan

- Input: `python main.py --database-path data/example-runs/01-budget-replan.db run --topic "夏季防晒新品活动" --budget 10 --deadline "2030-10-30T18:00:00+08:00"`
- Actual status: `completed`
- Planner mode: `rule`
- Trace entries: `11`
- Database rows: `{'runs': 1, 'steps': 6, 'tool_results': 6, 'replans': 1, 'saved_plans': 1, 'traces': 11}`

## 02-no-feasible-plan

- Input: `python main.py --database-path data/example-runs/02-no-feasible-plan.db run --topic "低预算活动测试" --budget 7 --deadline "2030-10-30T18:00:00+08:00"`
- Actual status: `partial`
- Planner mode: `rule`
- Trace entries: `10`
- Database rows: `{'runs': 1, 'steps': 5, 'tool_results': 5, 'replans': 1, 'saved_plans': 0, 'traces': 10}`

## 03-tool-failure-retry

- Input: `python main.py --database-path data/example-runs/03-tool-failure-retry.db demo --scenario tool-failure --fail-tool estimate_cost --fail-on-attempt 1`
- Actual status: `completed`
- Planner mode: `rule`
- Trace entries: `9`
- Database rows: `{'runs': 1, 'steps': 4, 'tool_results': 5, 'replans': 0, 'saved_plans': 1, 'traces': 9}`
