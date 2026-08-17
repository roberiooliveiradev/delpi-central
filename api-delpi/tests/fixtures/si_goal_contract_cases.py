"""SI goal triad contract cases for api-delpi (local copy — no cross-app import)."""

from __future__ import annotations

from typing import Any

# Partial month payload: registered ≠ period comparable (matrix B / G / H).
PARTIAL_SI_META_PAYLOAD: dict[str, Any] = {
    "goal_value": 10.0,
    "comparable_goal": 5.0,
    "reference_goal": 10.0,
    "value": 5.0,
    "goal_label": "Meta",
    "goal_mode": "standard",
    "goal_period_kind": "partial",
    "goal_period_partial": True,
    "goal_aggregation": "sum",
    "has_goal": True,
    "has_value": True,
}

SI_GOAL_FIELD_LABELS_PT: dict[str, str] = {
    "goal_value": "Meta cadastrada",
    "comparable_goal": "Meta do período",
    "reference_goal": "Meta mês (referência)",
}

HUB_ENRICH_CASES: tuple[dict[str, Any], ...] = (
    {
        "id": "kaizen_ideas",
        "source_key": "quality_kaizen_ideas",
        "summary_key": "ideas_goal",
        "payload": {"ideas_goal": {"total_kaizens": 3}},
    },
    {
        "id": "transforma_plus",
        "source_key": "engineering_transforma_plus",
        "summary_key": None,
        "payload": {"score": 8.0},
    },
    {
        "id": "lmp_otd",
        "source_key": "supplies_otd",
        "summary_key": "summary",
        "payload": {"summary": {"otd_percentage": 88.0}},
    },
    {
        "id": "ppm_internal",
        "source_key": "quality_ppm_internal",
        "summary_key": None,
        "payload": {"ppm": 835.0},
    },
)
