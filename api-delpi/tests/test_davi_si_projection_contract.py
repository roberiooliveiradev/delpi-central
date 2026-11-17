"""DAVI-SI-W013-READ-OUTPUT-PROJECTION-RECOVERY-01 — projection contract.

Fail-first regression for the incident:

  * ``list_si_admin_departments`` returned ``{"items": [{}, {}]}`` because
    ``approvedResponseFields: ["items"]`` runs in flat mode and filters a key
    ``items`` *inside* each item dict.
  * ``get_si_departments_tree`` returned ``data: null / truncated: true``
    because flat mode leaf-copies the whole raw ``scopes`` subtree and the
    payload exceeds the byte budget (``RESPONSE_TOO_LARGE``).

For every W013 operation we project a representative owner-shaped payload
through ``apply_approved_field_projection`` + ``bound_response_payload`` and
assert that authorized business content survives (non-empty items, populated
identifiers, preserved hierarchy), while non-approved fields stay dropped.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.application.external_capabilities.dynamic_information.content_loader import (
    load_external_read_allowlist,
)
from app.application.external_capabilities.dynamic_information.projection import (
    apply_approved_field_projection,
    bound_response_payload,
)

_API_ROOT = Path(__file__).resolve().parents[1]

MAX_BYTES = 65536
MAX_ITEMS = 50


def _approved_fields(operation_id: str) -> list[str]:
    allowlist = load_external_read_allowlist()
    for entry in allowlist["operations"]:
        if entry["operationId"] == operation_id:
            return list(entry.get("approvedResponseFields") or [])
    raise AssertionError(f"operation {operation_id} not in allowlist")


def _project_and_bound(payload: dict | list, operation_id: str) -> dict:
    projected = apply_approved_field_projection(
        payload, approved_fields=_approved_fields(operation_id)
    )
    return bound_response_payload(projected, max_bytes=MAX_BYTES, max_items=MAX_ITEMS)


def _resolve(data, path: str):
    """Resolve a dotted check path (``items.0.department_id``) or None."""
    node = data
    for part in path.split("."):
        if isinstance(node, list):
            try:
                node = node[int(part)]
            except (ValueError, IndexError):
                return None
        elif isinstance(node, dict):
            node = node.get(part)
        else:
            return None
    return node


# ---------------------------------------------------------------------------
# Representative owner payloads (verified against SI API use cases/repos)
# ---------------------------------------------------------------------------

ADMIN_DEPARTMENT_ITEM = {
    "department_id": "DEP-OPS",
    "department_name": "Operações",
    "short_name": "OPS",
    "strategic_summary": "Resumo estratégico",
    "headline_goal": "Meta principal",
    "supporting_focus": "Foco",
    "weight_pct": 20.0,
    "aggregation_mode": "consolidated",
    "is_active": True,
    "display_order": 1,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-06-01T00:00:00Z",
    "created_by_email": "a@b.c",
    "updated_by_email": "a@b.c",
}

ADMIN_INDICATOR_ITEM = {
    "indicator_id": "IND-01",
    "department_id": "DEP-OPS",
    "indicator_name": "OTIF",
    "weight_pct": 50.0,
    "scope_type": "department",
    "performance_direction": "higher_is_better",
    "strategic_description": "Entregas no prazo",
    "source_key": "otif",
    "value_unit": "%",
    "value_prefix": None,
    "value_suffix": "%",
    "value_decimals": 2,
    "branch_value_aggregation": "average",
    "is_active": True,
    "display_order": 1,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-06-01T00:00:00Z",
    "created_by_email": "a@b.c",
    "updated_by_email": "a@b.c",
}

DEPT_LIST_ITEM = {
    "id": "DEP-OPS",
    "name": "Operações",
    "short_name": "OPS",
    "weight_pct": 20.0,
    "score": 72.5,
    "classification": "attention",
    "contribution": 14.5,
    "aggregation_mode": "consolidated",
    "strategic_summary": "Resumo",
    "variation": {"value": 1.2, "direction": "up"},
}

SI_INDICATOR_ITEM = {
    "department_id": "DEP-OPS",
    "department_name": "Operações",
    "indicator_id": "IND-01",
    "indicator_name": "OTIF",
    "weight_pct": 50.0,
    "goal_label": "Meta 2025",
    "goal_value": 95.0,
    "goal_periodicity": "monthly",
    "goal_mode": "monthly_curve",
    "monthly_targets": [{"month_number": 1, "target_value": 95.0}],
    "scope_type": "department",
    "performance_direction": "higher_is_better",
    "value": 90.0,
    "realized": {"01": 90.0},
    "score": 80.0,
    "gap": -5.0,
    "goals": {"01": 95.0},
    "gaps": {"01": -5.0},
    "has_value": True,
    "trend": "up",
    "classification": "good",
    "source": "erp",
    "value_unit": "%",
    "value_prefix": None,
    "value_suffix": "%",
    "value_decimals": 2,
}

TRENDS_PAYLOAD = {
    "competence": "2025-06",
    "current_igd": 70.0,
    "previous_igd": 68.0,
    "current_classification": "attention",
    "igd_series": [{"period": "2025-06", "value": 70.0, "classification": "attention"}],
    "departments": [
        {
            "id": "DEP-OPS",
            "name": "Operações",
            "current": 72.5,
            "previous": 71.0,
            "direction": "up",
            "last_step_direction": "up",
            "net_variation": 1.5,
            "best_score": 72.5,
            "worst_score": 70.0,
            "current_classification": "attention",
            "current_contribution": 14.5,
            "series": [
                {"period": "2025-06", "score": 72.5, "classification": "attention"}
            ],
        }
    ],
    "indicator_series_by_department_id": {
        "DEP-OPS": [
            {
                "indicator_id": "IND-01",
                "indicator_name": "OTIF",
                "weight_pct": 50.0,
                "goal_label": "Meta 2025",
                "goal_value": 95.0,
                "goal_periodicity": "monthly",
                "goal_mode": "standard",
                "monthly_targets": [],
                "scope_type": "department",
                "performance_direction": "higher_is_better",
                "strategic_description": "desc",
                "source": "erp",
                "series": [
                    {
                        "period": "2025-06",
                        "value": 90.0,
                        "score": 80.0,
                        "gap": -5.0,
                        "classification": "good",
                        "trend": "up",
                    }
                ],
            }
        ]
    },
    "errors": [],
    "partial_success": False,
    "months_requested": 6,
    "competences_requested": ["2025-06"],
    "competences_returned": ["2025-06"],
    "missing_competences": [],
}

TREE_SCOPE = {
    "scope_key": "consolidated",
    "scope_label": "Consolidado",
    "branch": None,
    "departments": {
        "items": [DEPT_LIST_ITEM],
        "errors": [],
        "partial_success": False,
    },
    "indicators": {
        "items": [SI_INDICATOR_ITEM],
        "errors": [],
        "partial_success": False,
    },
    "trends": TRENDS_PAYLOAD,
}

TREE_SNAPSHOT_SCOPE = {k: v for k, v in TREE_SCOPE.items() if k != "trends"}

DETAILS_INDICATOR = {
    "id": "IND-01",
    "name": "OTIF",
    "weight_pct": 50.0,
    "goal_label": "Meta 2025",
    "goal_value": 95.0,
    "goal_periodicity": "monthly",
    "goal_mode": "monthly_curve",
    "monthly_targets": [{"month_number": 1, "target_value": 95.0}],
    "strategic_description": "desc",
    "scope_type": "department",
    "performance_direction": "higher_is_better",
    "realized": {"01": 90.0},
    "has_value": True,
    "classification": "good",
    "score": 80.0,
    "gap": -5.0,
    "gaps": {"01": -5.0},
    "goals": {"01": 95.0},
    "trend": "up",
    "value_unit": "%",
    "value_prefix": None,
    "value_suffix": "%",
    "value_decimals": 2,
}

DEPARTMENT_DETAILS_PAYLOAD = {
    "id": "DEP-OPS",
    "name": "Operações",
    "short_name": "OPS",
    "weight_pct": 20.0,
    "score": 72.5,
    "classification": "attention",
    "contribution": 14.5,
    "aggregation_mode": "consolidated",
    "strategic_summary": "Resumo",
    "variation": {"value": 1.2, "direction": "up"},
    "units": [
        {
            "unit_id": "01",
            "unit_name": "Filial 01",
            "score": 72.5,
            "has_value": True,
            "classification": "attention",
        }
    ],
    "indicators": [DETAILS_INDICATOR],
    "errors": [],
    "partial_success": False,
}

ALERTS_PAYLOAD = {
    "competence": "2025-06",
    "executive_alerts": [
        {
            "title": "IGD em atenção",
            "severity": "warning",
            "impact": "Impacto executivo",
            "recommendation": "Recomendação",
        }
    ],
    "department_alerts": [
        {
            "department_id": "DEP-OPS",
            "department_name": "Operações",
            "severity": "warning",
            "score": 72.5,
            "previous_score": 71.0,
            "variation": 1.5,
            "classification": "attention",
            "contribution": 14.5,
            "message": "msg",
        }
    ],
    "indicator_alerts": [
        {
            "department_id": "DEP-OPS",
            "department_name": "Operações",
            "indicator_id": "IND-01",
            "indicator_name": "OTIF",
            "severity": "critical",
            "score": 55.0,
            "gap": -40.0,
            "classification": "critical",
            "source": "erp",
            "goal_label": "Meta 2025",
            "goal_value": 95.0,
            "goal_periodicity": "monthly",
            "goal_mode": "standard",
            "monthly_targets": [],
            "goals": {"01": 95.0},
            "performance_direction": "higher_is_better",
            "value_unit": "%",
            "value_prefix": None,
            "value_suffix": "%",
            "value_decimals": 2,
            "message": "msg",
        }
    ],
    "errors": [],
    "partial_success": False,
}

EXEC_SUMMARY = {
    "competence": "2025-06",
    "igd": 70.0,
    "igd_exact": 70.123,
    "classification": "attention",
    "variation": {"value": 2.0, "direction": "up", "vs_label": "vs período anterior"},
    "departments": [
        {
            "id": "DEP-OPS",
            "name": "Operações",
            "short_name": "OPS",
            "weight_pct": 20.0,
            "score": 72.5,
            "contribution": 14.5,
            "trend": "up",
            "strategic_summary": "Resumo",
            "key_indicators": ["OTIF"],
            "executive_goal": "goal",
            "variation": {"value": 1.2, "direction": "up"},
        }
    ],
    "alerts_summary": [],
    "errors": [],
    "partial_success": False,
}

SETTINGS_PAYLOAD = {
    "weights": {
        "items": [
            {
                "department_id": "DEP-OPS",
                "department_name": "Operações",
                "weight_pct": 20.0,
            }
        ]
    },
    "goals": {
        "items": [
            {
                "department_id": "DEP-OPS",
                "department_name": "Operações",
                "headline_goal": "goal",
                "supporting_focus": "focus",
            }
        ]
    },
    "parameters": {"items": [{"key": "months_window", "value": 6}]},
    "governance": {"items": [{"key": "notes", "value": "n"}]},
    "meta": {
        "source": "postgres-plugins",
        "updated_at": "2025-06-01T00:00:00Z",
        "updated_by_email": "a@b.c",
    },
}

EXPORT_GOAL_ITEM = {
    "indicator_id": "IND-01",
    "indicator_name": "OTIF",
    "department_id": "DEP-OPS",
    "goal_year": 2025,
    "goal_label": "Meta 2025",
    "goal_value": 95.0,
    "goal_periodicity": "monthly",
    "goal_mode": "standard",
    "goal_scope_branch": "",
    "version": 1,
    "is_active": True,
    "valid_from": "2025-01-01",
    "valid_to": None,
    "notes": None,
    "monthly_targets": [{"month_number": 1, "target_value": 95.0}],
}


# ---------------------------------------------------------------------------
# Contract expectations: op -> (fixture, required check paths)
# ---------------------------------------------------------------------------

def _paged(items: list[dict]) -> dict:
    return {"items": list(items), "total": 7, "limit": 2, "offset": 0}


CASES: list[tuple[str, dict, list[str]]] = [
    (
        "list_si_admin_departments",
        _paged([ADMIN_DEPARTMENT_ITEM, dict(ADMIN_DEPARTMENT_ITEM)]),
        [
            "items.0.department_id",
            "items.0.department_name",
            "items.0.weight_pct",
            "items.1.department_id",
            "total",
        ],
    ),
    (
        "list_si_admin_department_indicators",
        _paged([ADMIN_INDICATOR_ITEM]),
        [
            "items.0.indicator_id",
            "items.0.indicator_name",
            "items.0.scope_type",
            "items.0.performance_direction",
        ],
    ),
    (
        "list_si_goal_years_overview",
        _paged(
            [
                {
                    "goal_year": 2025,
                    "total_versions": 30,
                    "total_active_versions": 12,
                    "total_active_indicators": 10,
                }
            ]
        ),
        [
            "items.0.goal_year",
            "items.0.total_versions",
            "items.0.total_active_versions",
            "items.0.total_active_indicators",
        ],
    ),
    (
        "list_si_settings_audit",
        {
            "items": [
                {
                    "id": "evt-1",
                    "event_type": "settings.updated",
                    "entity_key": "weights",
                    "payload_before": {"weight_pct": 10},
                    "payload_after": {"weight_pct": 20},
                    "changed_by_user_id": "u1",
                    "changed_by_email": "a@b.c",
                    "created_at": "2025-06-01T00:00:00Z",
                }
            ]
        },
        [
            "items.0.id",
            "items.0.event_type",
            "items.0.entity_key",
            "items.0.payload_after.weight_pct",
            "items.0.changed_by_email",
        ],
    ),
    (
        "list_si_change_requests",
        _paged(
            [
                {
                    "id": "cr-1",
                    "request_code": "CR-2025-001",
                    "title": "Atualizar meta",
                    "description": "desc",
                    "target_block": "goals",
                    "proposed_payload": {"goal_value": 100},
                    "status": "submitted",
                    "created_by_user_id": "u1",
                    "created_by_email": "a@b.c",
                    "submitted_by_user_id": "u1",
                    "submitted_by_email": "a@b.c",
                    "submitted_at": "2025-06-01T00:00:00Z",
                    "created_at": "2025-06-01T00:00:00Z",
                    "updated_at": "2025-06-01T00:00:00Z",
                }
            ]
        ),
        [
            "items.0.request_code",
            "items.0.title",
            "items.0.target_block",
            "items.0.proposed_payload.goal_value",
            "items.0.status",
            "total",
        ],
    ),
    (
        "get_si_department_details",
        DEPARTMENT_DETAILS_PAYLOAD,
        [
            "id",
            "name",
            "weight_pct",
            "score",
            "variation.value",
            "units.0.unit_id",
            "units.0.score",
            "indicators.0.id",
            "indicators.0.goal_value",
            "indicators.0.realized",
        ],
    ),
    (
        "get_si_departments_tree",
        {
            "competence": "2025-06",
            "igd": 70.0,
            "igd_exact": 70.123,
            "classification": "attention",
            "months": 6,
            "scopes": [TREE_SCOPE],
            "meta": {"source": "postgres-plugins", "scope_count": 1},
        },
        [
            "competence",
            "igd",
            "scopes.0.scope_key",
            "scopes.0.departments.items.0.id",
            "scopes.0.departments.items.0.score",
            "scopes.0.indicators.items.0.indicator_id",
            "scopes.0.indicators.items.0.value",
            "scopes.0.trends.current_igd",
        ],
    ),
    (
        "get_si_departments_tree_snapshot",
        {
            "competence": "2025-06",
            "igd": 70.0,
            "igd_exact": 70.123,
            "classification": "attention",
            "errors": [],
            "partial_success": False,
            "alerts_summary": [],
            "scopes": [TREE_SNAPSHOT_SCOPE],
            "meta": {"source": "postgres-plugins", "scope_count": 1},
        },
        [
            "competence",
            "igd",
            "scopes.0.scope_key",
            "scopes.0.departments.items.0.id",
            "scopes.0.indicators.items.0.indicator_id",
        ],
    ),
    (
        "get_si_departments_tree_trends",
        {
            "competence": "2025-06",
            "months": 6,
            "scopes": [
                {
                    "scope_key": "consolidated",
                    "scope_label": "Consolidado",
                    "branch": None,
                    "trends": TRENDS_PAYLOAD,
                }
            ],
            "meta": {"source": "postgres-plugins", "scope_count": 1},
        },
        [
            "competence",
            "months",
            "scopes.0.scope_key",
            "scopes.0.trends.current_igd",
            "scopes.0.trends.departments.0.id",
        ],
    ),
    (
        "get_si_alerts",
        ALERTS_PAYLOAD,
        [
            "competence",
            "executive_alerts.0.title",
            "executive_alerts.0.severity",
            "department_alerts.0.department_id",
            "department_alerts.0.score",
            "indicator_alerts.0.indicator_id",
            "indicator_alerts.0.gap",
            "indicator_alerts.0.message",
        ],
    ),
    (
        "get_si_trends",
        TRENDS_PAYLOAD,
        [
            "competence",
            "current_igd",
            "igd_series.0.period",
            "departments.0.id",
            "departments.0.current",
            "departments.0.series.0.score",
            "indicator_series_by_department_id",
            "months_requested",
        ],
    ),
    (
        "get_si_presentation",
        {
            "executive_summary": EXEC_SUMMARY,
            "departments_overview": [
                {
                    "id": "DEP-OPS",
                    "name": "Operações",
                    "short_name": "OPS",
                    "weight_pct": 20.0,
                    "score": 72.5,
                    "classification": "attention",
                    "contribution": 14.5,
                    "aggregation_mode": "consolidated",
                    "strategic_summary": "Resumo",
                    "variation": {"value": 1.2, "direction": "up"},
                }
            ],
            "department_details_by_id": {"DEP-OPS": DEPARTMENT_DETAILS_PAYLOAD},
            "indicators_by_department_id": {"DEP-OPS": [SI_INDICATOR_ITEM]},
            "alerts": ALERTS_PAYLOAD,
            "trends": TRENDS_PAYLOAD,
            "meta": {"partial_success": False, "errors": []},
        },
        [
            "executive_summary.igd",
            "executive_summary.departments.0.id",
            "departments_overview.0.id",
            "departments_overview.0.score",
            "department_details_by_id",
            "indicators_by_department_id",
            "alerts.competence",
            "trends.current_igd",
            "meta.partial_success",
        ],
    ),
    (
        "get_si_cache_refresh_status",
        {
            "running": False,
            "last_started_at": "2025-06-01T00:00:00Z",
            "last_completed_at": "2025-06-01T00:00:01Z",
            "last_duration_ms": 1234,
            "last_periods_upserted": 3,
            "last_error": None,
        },
        ["running", "last_completed_at", "last_periods_upserted"],
    ),
    (
        "get_si_job_status",
        {
            "job_id": "job-1",
            "state": "succeeded",
            "phase": "done",
            "progress_pct": 100,
            "message": "ok",
            "created_at": "2025-06-01T00:00:00Z",
            "updated_at": "2025-06-01T00:00:01Z",
            "snapshot": {"large": "embedded"},
            "trends": {"large": "embedded"},
            "error": None,
        },
        ["job_id", "state", "phase", "progress_pct", "message"],
    ),
    (
        "get_si_settings",
        SETTINGS_PAYLOAD,
        [
            "weights.items.0.department_id",
            "weights.items.0.weight_pct",
            "goals.items.0.headline_goal",
            "parameters.items",
            "meta.source",
        ],
    ),
    (
        "export_si_admin_config",
        {
            "schema_version": 1,
            "exported_at": "2025-06-01T00:00:00Z",
            "departments": [ADMIN_DEPARTMENT_ITEM],
            "department_indicators": [ADMIN_INDICATOR_ITEM],
            "indicator_goals": [EXPORT_GOAL_ITEM],
            "module_settings": {"parameters": {}, "governance": {}},
        },
        [
            "schema_version",
            "departments.0.department_id",
            "departments.0.weight_pct",
            "department_indicators.0.indicator_id",
            "indicator_goals.0.indicator_id",
            "indicator_goals.0.goal_value",
            "indicator_goals.0.monthly_targets.0.month_number",
            "module_settings",
        ],
    ),
]


@pytest.mark.parametrize(
    "operation_id,payload,required_paths",
    CASES,
    ids=[c[0] for c in CASES],
)
def test_w013_projection_preserves_owner_content(operation_id, payload, required_paths):
    bound = _project_and_bound(payload, operation_id)
    assert bound["data"] is not None, (
        f"{operation_id}: projected payload was dropped "
        f"(error={bound.get('error')}, truncated={bound.get('truncated')})"
    )
    data = bound["data"]
    for path in required_paths:
        value = _resolve(data, path)
        assert value is not None and value != {}, (
            f"{operation_id}: required projected field '{path}' missing/empty "
            f"in {json.dumps(data, ensure_ascii=False, default=str)[:400]}"
        )
        if isinstance(value, dict) and not value:
            pytest.fail(f"{operation_id}: '{path}' projected to empty object")


def test_case_a_admin_departments_items_not_empty_objects():
    """Incident case A: ``items`` entries must not project to ``{}``."""
    bound = _project_and_bound(
        _paged([ADMIN_DEPARTMENT_ITEM, dict(ADMIN_DEPARTMENT_ITEM)]),
        "list_si_admin_departments",
    )
    data = bound["data"]
    assert data is not None
    items = data["items"]
    assert items and all(isinstance(i, dict) and i for i in items), (
        f"items projected to empty objects: {items}"
    )
    assert items[0]["department_id"] == "DEP-OPS"


def test_case_b_tree_not_dropped_by_budget():
    """Incident case B: tree must survive the byte budget, not ``data: null``."""
    # Inflate the tree so a raw whole-subtree copy would exceed the budget.
    big_departments = {
        "items": [dict(DEPT_LIST_ITEM, id=f"DEP-{i:03d}") for i in range(30)],
        "errors": [],
        "partial_success": False,
    }
    big_indicators = {
        "items": [
            dict(SI_INDICATOR_ITEM, indicator_id=f"IND-{i:03d}") for i in range(40)
        ],
        "errors": [],
        "partial_success": False,
    }
    payload = {
        "competence": "2025-06",
        "igd": 70.0,
        "igd_exact": 70.123,
        "classification": "attention",
        "months": 6,
        "scopes": [
            {
                "scope_key": "consolidated",
                "scope_label": "Consolidado",
                "branch": None,
                "departments": big_departments,
                "indicators": big_indicators,
                "trends": TRENDS_PAYLOAD,
            }
        ],
        "meta": {"source": "postgres-plugins", "scope_count": 1},
    }
    bound = _project_and_bound(payload, "get_si_departments_tree")
    assert bound["data"] is not None, (
        "departments_tree exceeded budget and was nulled "
        "(RESPONSE_TOO_LARGE via raw container copy)"
    )
    assert bound["data"]["scopes"][0]["departments"]["items"], (
        "departments list lost in projection"
    )
    assert bound["data"]["scopes"][0]["departments"]["items"][0]["id"], (
        "department identifiers lost in projection"
    )


def test_projection_still_drops_non_approved_fields():
    """Fail-closed guarantee: non-allowlisted fields never leak."""
    payload = dict(ADMIN_DEPARTMENT_ITEM)
    payload["internal_secret"] = "should-not-leak"
    bound = _project_and_bound({"items": [payload]}, "list_si_admin_departments")
    assert bound["data"] is not None
    assert "internal_secret" not in json.dumps(bound["data"])
