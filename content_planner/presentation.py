"""Terminal presentation helpers."""

from __future__ import annotations

import json

from content_planner.models import PlanningResult


def render_json(result: PlanningResult) -> str:
    return json.dumps(result.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)
