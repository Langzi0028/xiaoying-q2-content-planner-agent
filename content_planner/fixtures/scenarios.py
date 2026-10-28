"""Deterministic candidate data for the written-assessment demos."""

from __future__ import annotations

from content_planner.models import Candidate


OVER_BUDGET_REPLAN_CANDIDATES = (
    Candidate(
        candidate_id="candidate_premium",
        name="高制作成本短片方案",
        asset_id="asset_premium",
        base_cost=12,
        duration_minutes=90,
    ),
    Candidate(
        candidate_id="candidate_low_cost",
        name="轻量图文短视频方案",
        asset_id="asset_low_cost",
        base_cost=8,
        duration_minutes=45,
    ),
)

TOOL_FAILURE_CANDIDATES = (
    Candidate(
        candidate_id="candidate_reliable",
        name="可恢复估算故障的标准方案",
        asset_id="asset_reliable",
        base_cost=8,
        duration_minutes=40,
    ),
)

NO_FEASIBLE_CANDIDATES = (
    Candidate(
        candidate_id="candidate_minimum_cost",
        name="最低可行成本方案",
        asset_id="asset_minimum_cost",
        base_cost=12,
        duration_minutes=35,
    ),
    Candidate(
        candidate_id="candidate_expensive",
        name="高成本备选方案",
        asset_id="asset_expensive",
        base_cost=15,
        duration_minutes=50,
    ),
)

DEADLINE_REPLAN_CANDIDATES = (
    Candidate(
        candidate_id="candidate_slow",
        name="制作周期过长的方案",
        asset_id="asset_slow",
        base_cost=8,
        duration_minutes=120,
    ),
    Candidate(
        candidate_id="candidate_fast",
        name="满足截止时间的快速方案",
        asset_id="asset_fast",
        base_cost=8,
        duration_minutes=30,
    ),
)
