from __future__ import annotations

from datetime import datetime
from typing import Any

PLAN_SELECT = """
    SELECT p.id,
           p.code,
           p.title,
           p.customer_name,
           p.customer_contact,
           p.source_type,
           p.source_reference,
           p.product_code,
           p.product_description,
           p.batch_number,
           p.reported_problem,
           p.detected_at,
           p.reported_at,
           p.severity,
           p.status,
           p.created_by_user_id,
           p.owner_user_id,
           p.department,
           p.problem_category,
           p.symptom_tags,
           p.root_cause_category,
           p.failure_mode,
           p.effectiveness_status,
           p.effectiveness_verified_at,
           p.effectiveness_notes,
           p.recurrence_key,
           p.created_at,
           p.updated_at,
           p.closed_at
      FROM quality.quality_action_plans p
"""


def serialize_row(row: dict[str, Any] | None, *, id_keys: tuple[str, ...] = ("id",)) -> dict[str, Any] | None:
    if row is None:
        return None
    result = dict(row)
    for key in id_keys:
        if result.get(key) is not None:
            result[key] = str(result[key])
    for key, value in list(result.items()):
        if isinstance(value, datetime):
            result[key] = value.isoformat()
    return result


def serialize_plan_row(row: dict[str, Any]) -> dict[str, Any]:
    result = serialize_row(row, id_keys=("id",)) or {}
    if result.get("symptom_tags") is None:
        result["symptom_tags"] = []
    return result
