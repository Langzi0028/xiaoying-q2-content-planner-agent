# Xiaoying Q2 Content Planner Agent

一个面向“小影科技笔试题第二题”的 Python 命令行内容任务规划 Agent。它采用 LangGraph 管理状态化执行，SQLite 保存运行审计与 checkpoint，并预留 LangChain + OpenAI-compatible 中转站模型适配。

项目按规范将应用源码放在 `src/content_planner/`。为便于审核者直接运行，根目录 `main.py` 会显式加入 `src/` 后再启动 CLI，因此不需要 editable install 或额外设置 `PYTHONPATH`。

## Quick Start

```powershell
# Activate your Conda environment first, then run from the project root.
python -m pip install -r requirements.txt
python main.py demo --scenario over-budget-replan
python -m pytest -v
```

The only supported CLI entry point is `python main.py`.

## Gateway Configuration

Copy `.env.example` to `.env`, then add your OpenAI-compatible gateway values. The program loads the project-root `.env` automatically and does not override values defined by PyCharm or the shell. `.env` is ignored by Git.

If no complete LLM configuration is available, the CLI prints a notice to stderr and continues with the built-in rule planner. If a configured LLM request fails, it prints the exception type and continues with the rule fallback. The final JSON remains on stdout in both cases.

## Assessment Coverage

- 预算为 10 时，先记录成本 12 的候选，再自动重规划到成本 8 的候选并保存。
- 工具注入失败时，失败工具结果保持失败；此前成功的脚本步骤不会被重复执行。
- 没有可行方案时不保存，并输出最低成本与预算缺口。
- `run` 路径先校验输入，再经 LangGraph 执行，并使用同一个 SQLite 文件保存 checkpoint。
- 相同幂等键会返回已有运行，不产生新的工具调用。

## Review Entry Point

1. Read `docs/01-requirements.md`, `docs/02-solution.md`, and `docs/03-evaluation.md`.
2. Run `python -m pytest -v`.
3. Inspect three actual local evidence sets under `examples/`.

## Limitations And Secret Policy

- Local fixtures intentionally simulate the business tools for repeatable review.
- A constrained live-LLM replacement decision is recorded in `examples/04-live-llm.json`; it proves the bounded decision path, not broad model quality.
- Never commit `.env`, API keys, private gateway URLs, or generated SQLite databases. Use `.env.example` as the only configuration template.

Detailed design is in `docs/02-solution.md`; demo commands are in `docs/demo-script.md`.
