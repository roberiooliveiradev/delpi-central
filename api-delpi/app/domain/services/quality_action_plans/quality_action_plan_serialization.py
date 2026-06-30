from __future__ import annotations

from datetime import datetime
from typing import Any

from app.domain.services.quality_action_plans.quality_action_plan_sla_service import (
    enrich_plan_row_sla,
)

PLAN_SELECT = """
    SELECT p.id,
           p.code,
           p.title,
           p.customer_name,
           p.customer_code,
           p.customer_store,
           p.customer_contact,
           p.nonconformity_scope,
           p.customer_template,
           p.export_template_key,
           p.client_nc_registry,
           p.template_payload,
           p.source_type,
           p.source_reference,
           p.product_code,
           p.product_description,
           p.customer_product_reference,
           p.batch_number,
           p.reported_problem,
           p.detected_at,
           p.reported_at,
           p.severity,
           p.status,
           p.created_by_user_id,
           p.owner_user_id,
           p.branch_code,
           p.department,
           p.problem_category,
           p.symptom_tags,
           p.root_cause_category,
           p.failure_mode,
           p.effectiveness_status,
           p.effectiveness_verified_at,
           p.effectiveness_notes,
           p.effectiveness_approval_status,
           p.effectiveness_proposed_status,
           p.effectiveness_submitted_at,
           p.effectiveness_submitted_by,
           p.effectiveness_submitted_by_name,
           p.effectiveness_reviewed_at,
           p.effectiveness_reviewed_by,
           p.effectiveness_rejection_reason,
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
    if result.get("template_payload") is None:
        result["template_payload"] = {}
    return enrich_plan_row_sla(result)
