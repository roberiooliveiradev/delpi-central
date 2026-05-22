from si_app.application.dto.strategic_indicators.catalog_models import (
    StrategicDepartmentCatalogItem,
    StrategicIndicatorCatalogItem,
)
from si_app.application.services.strategic_indicators.catalog_inputs_fingerprint import (
    build_catalog_inputs_fingerprint,
)
from si_app.application.services.strategic_indicators.strategic_indicators_snapshot_models import (
    StrategicIndicatorsCatalogSnapshot,
)


def _department() -> StrategicDepartmentCatalogItem:
    return StrategicDepartmentCatalogItem(
        department_id="producao",
        department_name="Produção",
        short_name="Prod",
        weight_pct=10.0,
        strategic_summary="",
        aggregation_mode="consolidated",
    )


def _indicator(**overrides) -> StrategicIndicatorCatalogItem:
    base = {
        "indicator_id": "ind-1",
        "department_id": "producao",
        "indicator_name": "OEE",
        "weight_pct": 5.0,
        "goal_label": "Meta",
        "goal_value": 90.0,
        "goal_periodicity": "monthly",
        "goal_mode": "standard",
        "monthly_targets": [],
        "scope_type": "consolidated",
        "performance_direction": "higher_is_better",
        "branch_goals": {},
        "resolved_goal_scope_branch": "",
        "has_resolved_goal": True,
    }
    base.update(overrides)
    return StrategicIndicatorCatalogItem(**base)


def _catalog(*, indicators: list[StrategicIndicatorCatalogItem]) -> StrategicIndicatorsCatalogSnapshot:
    return StrategicIndicatorsCatalogSnapshot(
        departments_catalog=[_department()],
        indicators_catalog=list(indicators),
        goals_by_department={"producao": "90"},
    )


def test_fingerprint_changes_when_scope_type_changes() -> None:
    consolidated = _catalog(indicators=[_indicator(scope_type="consolidated")])
    per_unit = _catalog(indicators=[_indicator(scope_type="per_unit")])

    assert build_catalog_inputs_fingerprint(consolidated) != build_catalog_inputs_fingerprint(
        per_unit
    )


def test_fingerprint_changes_when_branch_goals_change() -> None:
    without_branch = _catalog(indicators=[_indicator(branch_goals={})])
    with_branch = _catalog(
        indicators=[
            _indicator(
                branch_goals={
                    "01": {"goal_value": 80.0, "goal_label": "Filial 01"},
                }
            )
        ]
    )

    assert build_catalog_inputs_fingerprint(without_branch) != build_catalog_inputs_fingerprint(
        with_branch
    )
