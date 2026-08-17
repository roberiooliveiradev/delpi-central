"""Local SI goal triad fixtures for tv-dashboard-api (no cross-app import)."""

from __future__ import annotations

SI_GOAL_FIELD_LABELS_PT: dict[str, str] = {
    "comparable_goal": "Meta do período",
    "goal_value": "Meta cadastrada",
    "reference_goal": "Meta mês (referência)",
}

# Sample of SI meta operationIds for parametrized enrich (matrix F/G).
SI_META_OPERATION_IDS_SAMPLE: tuple[str, ...] = (
    "get_si_indicator_quality_ppm_external_meta",
    "get_si_indicator_quality_kaizen_ideas_meta",
    "get_si_indicator_commercial_rol_meta",
    "get_si_indicator_engineering_transforma_plus_meta",
    "get_si_indicator_supplies_otd_meta",
)

PARTIAL_DISTINCT_META_DATA: dict = {
    "value": 4.39,
    "comparable_goal": 4.39,
    "goal_value": 8.0,
    "reference_goal": 8.0,
    "value_decimals": 2,
    "has_value": True,
}
