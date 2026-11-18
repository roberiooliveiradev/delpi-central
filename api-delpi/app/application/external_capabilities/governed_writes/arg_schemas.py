"""Argument schemas for governed write capabilities (discovery contract).

Published by ``get_context(action="schema", capability=<write cap>)`` so
the model can construct valid PREPARE arguments without guessing — the
closed vocabularies in ``si_goal_capabilities`` / ``si_admin_capabilities``
remain the authoritative enforcement (these schemas are descriptive and
fail-closed validation still applies server-side).
"""

from __future__ import annotations

from typing import Any

from app.application.external_capabilities.governed_writes.si_goal_capabilities import (
    SI_GOAL_WRITE_CAPABILITIES,
)
from app.application.external_capabilities.governed_writes.si_admin_capabilities import (
    SI_ADMIN_WRITE_CAPABILITIES,
)
from app.application.external_capabilities.governed_writes.si_w014_capabilities import (
    SI_W014_WRITE_CAPABILITIES,
)
from app.application.external_capabilities.governed_writes.si_w015_capabilities import (
    SI_W015_DELETE_CAPABILITIES,
    SI_W015_WRITE_CAPABILITIES,
)

_STR = {"type": "string"}
_NUM = {"type": "number"}
_INT = {"type": "integer"}
_BOOL = {"type": "boolean"}
_OBJ = {"type": "object"}
_ARR = {"type": "array"}

_DEPT_FIELDS = {
    "department_name": _STR,
    "short_name": _STR,
    "strategic_summary": _STR,
    "headline_goal": _STR,
    "supporting_focus": _STR,
    "weight_pct": {**_NUM, "minimum": 0, "maximum": 100},
    "aggregation_mode": {"type": "string", "enum": ["consolidated", "average_of_units"]},
    "display_order": _INT,
}
_IND_FIELDS = {
    "indicator_name": _STR,
    "weight_pct": {**_NUM, "minimum": 0, "maximum": 100},
    "scope_type": {"type": "string", "enum": ["consolidated", "per_unit"]},
    "performance_direction": {
        "type": "string",
        "enum": ["higher_is_better", "lower_is_better"],
    },
    "strategic_description": _STR,
    "source_key": _STR,
    "value_unit": _STR,
    "value_prefix": _STR,
    "value_suffix": _STR,
    "value_decimals": {**_INT, "minimum": 0, "maximum": 6},
    "display_order": _INT,
}
_GOAL_FIELDS = {
    "indicator_id": _STR,
    "goal_year": {**_INT, "minimum": 2020, "maximum": 2100},
    "goal_label": _STR,
    "goal_value": _NUM,
    "goal_periodicity": {
        "type": "string",
        "enum": ["monthly", "annual", "quarterly", "weekly"],
    },
    "goal_mode": {"type": "string", "enum": ["standard", "monthly_curve"]},
    "goal_scope_branch": {"type": "string", "enum": ["", "01", "02"]},
    "monthly_targets": _ARR,
    "valid_from": _STR,
    "valid_to": _STR,
    "notes": _STR,
}


def _schema(properties: dict, required: list[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": required,
    }


WRITE_CAPABILITY_ARG_SCHEMAS: dict[str, dict[str, Any]] = {
    # ---- W012 goals ---------------------------------------------------
    "si.goal.create": _schema(
        dict(_GOAL_FIELDS),
        ["indicator_id", "goal_year", "goal_label", "goal_periodicity"],
    ),
    "si.goal.update": _schema(
        {
            "goal_id": _STR,
            **_GOAL_FIELDS,
            "set_monthly_target": _OBJ,
        },
        ["goal_id"],
    ),
    "si.goal.activate": _schema(
        {"goal_id": _STR, "indicator_id": _STR, "goal_year": _INT},
        ["goal_id"],
    ),
    "si.goal.deactivate": _schema(
        {"goal_id": _STR, "indicator_id": _STR, "goal_year": _INT},
        ["goal_id"],
    ),
    # ---- W013-ACT departments ----------------------------------------
    "si.department.create": _schema(
        {"department_id": _STR, **_DEPT_FIELDS},
        ["department_id", "department_name", "short_name", "weight_pct", "aggregation_mode"],
    ),
    "si.department.update": _schema(
        {
            "department_id": _STR,
            "new_department_id": _STR,
            **_DEPT_FIELDS,
            "is_active": _BOOL,
        },
        ["department_id"],
    ),
    "si.department.activate": _schema(
        {"department_id": _STR}, ["department_id"]
    ),
    "si.department.deactivate": _schema(
        {"department_id": _STR}, ["department_id"]
    ),
    # ---- W013-ACT settings (full-replace) -----------------------------
    "si.settings.update": _schema(
        {
            "parameters": {
                "type": "object",
                "additionalProperties": False,
                "required": ["items"],
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["key", "label", "value"],
                            "properties": {
                                "key": _STR,
                                "label": _STR,
                                "value": _STR,
                            },
                        },
                    }
                },
            },
            "governance": {
                "type": "object",
                "additionalProperties": False,
                "required": ["items"],
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["key", "label", "value"],
                            "properties": {
                                "key": _STR,
                                "label": _STR,
                                "value": _STR,
                                "observation": _STR,
                            },
                        },
                    }
                },
            },
        },
        ["parameters", "governance"],
    ),
    # ---- W013-ACT indicators ------------------------------------------
    "si.indicator.create": _schema(
        {"department_id": _STR, "indicator_id": _STR, **_IND_FIELDS},
        ["department_id", "indicator_id", "indicator_name", "weight_pct", "scope_type"],
    ),
    "si.indicator.update": _schema(
        {
            "indicator_id": _STR,
            "new_indicator_id": _STR,
            **_IND_FIELDS,
            "is_active": _BOOL,
        },
        ["indicator_id"],
    ),
    "si.indicator.activate": _schema(
        {"indicator_id": _STR}, ["indicator_id"]
    ),
    "si.indicator.deactivate": _schema(
        {"indicator_id": _STR}, ["indicator_id"]
    ),
    # ---- W013-ACT change requests --------------------------------------
    "si.change_request.create": _schema(
        {
            "title": _STR,
            "description": _STR,
            "target_block": {
                "type": "string",
                "enum": [
                    "departments",
                    "department_indicators",
                    "indicator_goals",
                    "parameters.global",
                    "governance.notes",
                ],
            },
            "proposed_payload": _OBJ,
        },
        ["title", "description", "target_block", "proposed_payload"],
    ),
    "si.change_request.comment": _schema(
        {"change_request_id": _STR, "comment_text": _STR},
        ["change_request_id", "comment_text"],
    ),
    "si.change_request.submit": _schema(
        {"change_request_id": _STR}, ["change_request_id"]
    ),
    # ---- W014 bulk / operational --------------------------------------
    "si.goal.bulk_create": _schema(
        {
            "goal_year": {**_INT, "minimum": 2020, "maximum": 2100},
            "items": {
                "type": "array",
                "maxItems": 500,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "indicator_id",
                        "goal_label",
                        "goal_value",
                        "goal_periodicity",
                    ],
                    "properties": {
                        k: v for k, v in _GOAL_FIELDS.items() if k != "goal_year"
                    },
                },
            },
        },
        ["goal_year", "items"],
    ),
    "si.goal.duplicate_year": _schema(
        {
            "source_year": {**_INT, "minimum": 2020, "maximum": 2100},
            "target_year": {**_INT, "minimum": 2020, "maximum": 2100},
            "department_ids": {"type": "array", "items": _STR, "maxItems": 200},
            "overwrite_existing": _BOOL,
        },
        ["source_year", "target_year"],
    ),
    "si.goal.fill_missing": _schema(
        {
            "goal_year": {**_INT, "minimum": 2020, "maximum": 2100},
            "department_ids": {"type": "array", "items": _STR, "maxItems": 200},
            "copy_from_year": {**_INT, "minimum": 2020, "maximum": 2100},
        },
        ["goal_year"],
    ),
    "si.config.import_apply": _schema(
        {
            "bundle": _OBJ,
            "include_goals": _BOOL,
        },
        ["bundle"],
    ),
    "si.cache.refresh": _schema(
        {
            "competence": _STR,
            "trends_months": {**_INT, "minimum": 1, "maximum": 24},
        },
        [],
    ),
    "si.cache.invalidate": _schema({}, []),
    "si.job.tree_load": _schema(
        {
            "view_mode": {
                "type": "string",
                "enum": ["consolidated", "per_unit"],
            },
            "branch": _STR,
            "competence": _STR,
            "start_date": _STR,
            "end_date": _STR,
            "months": {**_INT, "minimum": 2, "maximum": 12},
        },
        [],
    ),
    "si.config.import_replace": _schema(
        {
            "bundle": _OBJ,
        },
        ["bundle"],
    ),
}

WRITE_CAPABILITY_META: dict[str, dict[str, str]] = {
    cap: {
        "entity": entity,
        "shape": "governed_write_prepare",
        "description": desc,
    }
    for cap, entity, desc in (
        ("si.goal.create", "indicator_goal", "Create a goal for an indicator."),
        ("si.goal.update", "indicator_goal", "Update fields of an existing goal."),
        ("si.goal.activate", "indicator_goal", "Activate a goal."),
        ("si.goal.deactivate", "indicator_goal", "Deactivate a goal."),
        ("si.department.create", "department", "Create a department."),
        ("si.department.update", "department", "Update an existing department."),
        ("si.department.activate", "department", "Activate a department."),
        ("si.department.deactivate", "department", "Deactivate a department (excludes it from IGD/tree aggregates; reversible)."),
        ("si.settings.update", "module_settings", "Full-replace of parameters.global + governance.notes; omitted items are removed."),
        ("si.indicator.create", "department_indicator", "Create an indicator in a department."),
        ("si.indicator.update", "department_indicator", "Update an existing indicator."),
        ("si.indicator.activate", "department_indicator", "Activate an indicator."),
        ("si.indicator.deactivate", "department_indicator", "Deactivate an indicator."),
        ("si.change_request.create", "change_request", "Create a change request proposal."),
        ("si.change_request.comment", "change_request", "Add a comment to a change request."),
        ("si.change_request.submit", "change_request", "Submit a draft change request."),
        ("si.goal.bulk_create", "indicator_goal", "Batch-create goals (≤500 items, per-scope OCC)."),
        ("si.goal.duplicate_year", "indicator_goal", "Copy goals from one year to another (digest-bound preview)."),
        ("si.goal.fill_missing", "indicator_goal", "Create goals only for indicators missing one in a year."),
        ("si.config.import_apply", "admin_config", "Apply an exported config bundle (merge only; replace is reserved)."),
        ("si.cache.refresh", "si_cache", "Schedule a materialized period_scores refresh."),
        ("si.cache.invalidate", "si_cache", "Wipe materialized snapshots and schedule a recompute."),
        ("si.job.tree_load", "tree_load_job", "Dispatch an async department-tree load job."),
        ("si.config.import_replace", "admin_config", "Destructive replace of the whole catalog from a bundle (wipes departments/indicators/goals in one transaction)."),
    )
}


def get_write_capability_schema(capability: str) -> dict[str, Any] | None:
    """Return the PREPARE argument schema for a governed write capability,
    or ``None`` when the id is not an approved write capability."""
    if capability not in (
        SI_GOAL_WRITE_CAPABILITIES
        | SI_ADMIN_WRITE_CAPABILITIES
        | SI_W014_WRITE_CAPABILITIES
        | SI_W015_WRITE_CAPABILITIES
    ):
        return None
    schema = WRITE_CAPABILITY_ARG_SCHEMAS.get(capability)
    if schema is None:
        return None
    return {**WRITE_CAPABILITY_META.get(capability, {}), **schema}


DELETE_CAPABILITY_ARG_SCHEMAS: dict[str, dict[str, Any]] = {
    "si.goal.delete": _schema(
        {"goal_id": _STR},
        ["goal_id"],
    ),
    "si.indicator.delete": _schema(
        {"indicator_id": _STR},
        ["indicator_id"],
    ),
    "si.department.delete": _schema(
        {"department_id": _STR},
        ["department_id"],
    ),
}

DELETE_CAPABILITY_META: dict[str, dict[str, str]] = {
    cap: {
        "entity": entity,
        "shape": "governed_write_prepare",
        "destructive": "true",
        "description": desc,
    }
    for cap, entity, desc in (
        ("si.goal.delete", "indicator_goal", "Hard-delete a goal and its monthly targets (irreversible; copied_from links are cleared)."),
        ("si.indicator.delete", "department_indicator", "Hard-delete an indicator and every goal version/target under it (irreversible)."),
        ("si.department.delete", "department", "Hard-delete a department, all its indicators and their goals (irreversible)."),
    )
}


def get_delete_capability_schema(capability: str) -> dict[str, Any] | None:
    """Return the PREPARE argument schema for a governed destructive
    capability, or ``None`` when the id is not an approved delete."""
    if capability not in SI_W015_DELETE_CAPABILITIES:
        return None
    schema = DELETE_CAPABILITY_ARG_SCHEMAS.get(capability)
    if schema is None:
        return None
    return {**DELETE_CAPABILITY_META.get(capability, {}), **schema}
