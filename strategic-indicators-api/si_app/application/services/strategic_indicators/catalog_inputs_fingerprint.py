from __future__ import annotations

import hashlib
import json

from si_app.application.services.strategic_indicators.strategic_indicators_snapshot_models import (
    StrategicIndicatorsCatalogSnapshot,
)
from si_app.shared.json_encoding import to_json_safe


def build_catalog_inputs_fingerprint(
    catalog: StrategicIndicatorsCatalogSnapshot,
) -> str:
    payload = to_json_safe(
        {
            "departments": sorted(
                [
                    {
                        "department_id": item.department_id,
                        "weight_pct": item.weight_pct,
                        "aggregation_mode": item.aggregation_mode,
                    }
                    for item in catalog.departments_catalog
                ],
                key=lambda row: row["department_id"],
            ),
            "indicators": sorted(
                [
                    {
                        "indicator_id": item.indicator_id,
                        "department_id": item.department_id,
                        "weight_pct": item.weight_pct,
                        "goal_value": item.goal_value,
                        "goal_label": item.goal_label,
                        "goal_periodicity": item.goal_periodicity,
                        "goal_mode": item.goal_mode,
                        "monthly_targets": item.monthly_targets,
                        "scope_type": item.scope_type,
                        "performance_direction": item.performance_direction,
                        "branch_goals": item.branch_goals,
                        "resolved_goal_scope_branch": item.resolved_goal_scope_branch,
                        "has_resolved_goal": item.has_resolved_goal,
                    }
                    for item in catalog.indicators_catalog
                ],
                key=lambda row: row["indicator_id"],
            ),
            "goals_by_department": dict(
                sorted(catalog.goals_by_department.items()),
            ),
        }
    )
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8"),
    ).hexdigest()
    return digest[:32]
