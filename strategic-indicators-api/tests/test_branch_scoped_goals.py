from __future__ import annotations

from si_app.application.dto.strategic_indicators.catalog_models import (
    StrategicDepartmentCatalogItem,
    StrategicIndicatorCalculatedValue,
    StrategicIndicatorCatalogItem,
    StrategicIndicatorMeasuredValue,
)
from si_app.domain.services.strategic_indicators_calculator import (
    StrategicIndicatorsCalculator,
)
from si_app.shared.branch_scoped_goals import (
    format_branch_scoped_goal_label,
    pick_primary_branch_goal,
)


def test_format_branch_scoped_goal_label() -> None:
    label = format_branch_scoped_goal_label(
        {
            "02": {"goal_label": "8 PDIs"},
            "01": {"goal_label": "15 PDIs"},
        }
    )

    assert label == "01: 15 PDIs | 02: 8 PDIs"


def test_pick_primary_branch_goal_prefers_filial_01() -> None:
    goal = pick_primary_branch_goal(
        {
            "02": {"goal_value": 8.0},
            "01": {"goal_value": 15.0},
        }
    )

    assert goal["goal_value"] == 15.0


def test_consolidated_score_averages_branch_scores() -> None:
    calculator = StrategicIndicatorsCalculator()
    indicator = StrategicIndicatorCatalogItem(
        indicator_id="hr-pdi",
        department_id="hr",
        indicator_name="PDIs ativos",
        weight_pct=10,
        goal_label="01: 15 | 02: 8",
        goal_value=15,
        goal_periodicity="monthly",
        scope_type="consolidated",
        performance_direction="higher_is_better",
        branch_goals={
            "01": {
                "goal_label": "15",
                "goal_value": 15.0,
                "goal_periodicity": "monthly",
                "goal_mode": "standard",
                "monthly_targets": [],
            },
            "02": {
                "goal_label": "8",
                "goal_value": 8.0,
                "goal_periodicity": "monthly",
                "goal_mode": "standard",
                "monthly_targets": [],
            },
        },
    )

    calculated = calculator.calculate_indicators(
        indicators_catalog=[indicator],
        measurements=[
            StrategicIndicatorMeasuredValue(
                indicator_id="hr-pdi",
                department_id="hr",
                value=9.5,
                source="portal_rh_pdi_count",
                unit_values={"01": 10.0, "02": 9.0},
            )
        ],
        competence="2026-04",
        start_date="01-04-2026",
        end_date="30-04-2026",
    )

    assert len(calculated) == 1
    assert calculated[0].score is not None
    assert calculated[0].score > 0
    assert calculated[0].classification != calculator.MISSING_VALUE_CLASSIFICATION


def test_department_consolidated_score_is_average_of_branch_idds() -> None:
    calculator = StrategicIndicatorsCalculator()
    catalog = [
        StrategicIndicatorCatalogItem(
            indicator_id="hr-pdi",
            department_id="hr",
            indicator_name="PDIs",
            weight_pct=50,
            goal_label="por unidade",
            goal_value=15,
            goal_periodicity="monthly",
            branch_goals={
                "01": {
                    "goal_value": 10.0,
                    "goal_periodicity": "monthly",
                    "goal_mode": "standard",
                    "monthly_targets": [],
                },
                "02": {
                    "goal_value": 10.0,
                    "goal_periodicity": "monthly",
                    "goal_mode": "standard",
                    "monthly_targets": [],
                },
            },
        ),
        StrategicIndicatorCatalogItem(
            indicator_id="hr-turnover",
            department_id="hr",
            indicator_name="Turnover",
            weight_pct=50,
            goal_label="por unidade",
            goal_value=5,
            goal_periodicity="monthly",
            performance_direction="lower_is_better",
            branch_goals={
                "01": {
                    "goal_value": 5.0,
                    "goal_periodicity": "monthly",
                    "goal_mode": "standard",
                    "monthly_targets": [],
                },
                "02": {
                    "goal_value": 5.0,
                    "goal_periodicity": "monthly",
                    "goal_mode": "standard",
                    "monthly_targets": [],
                },
            },
        ),
    ]
    measurements = [
        StrategicIndicatorMeasuredValue(
            indicator_id="hr-pdi",
            department_id="hr",
            value=10.0,
            source="test",
            unit_values={"01": 10.0, "02": 5.0},
        ),
        StrategicIndicatorMeasuredValue(
            indicator_id="hr-turnover",
            department_id="hr",
            value=2.5,
            source="test",
            unit_values={"01": 0.0, "02": 5.0},
        ),
    ]

    departments = calculator.calculate_departments(
        departments_catalog=[
            StrategicDepartmentCatalogItem(
                department_id="hr",
                department_name="RH",
                short_name="RH",
                weight_pct=15,
                strategic_summary="",
                aggregation_mode="average_of_units",
            )
        ],
        indicators_catalog=catalog,
        measurements=measurements,
        competence="2026-04",
        start_date="01-04-2026",
        end_date="30-04-2026",
    )

    assert len(departments) == 1

    # Filial 01: PDI 10 + Turnover 10 → IDD 10 | Filial 02: PDI 5 + Turnover 10 → IDD 7,5
    assert departments[0].score == 8.75

    calculated = calculator.calculate_indicators(
        indicators_catalog=catalog,
        measurements=measurements,
        competence="2026-04",
        start_date="01-04-2026",
        end_date="30-04-2026",
    )
    assert calculated[0].unit_gaps == {"01": 0.0, "02": 5.0}


def test_unit_goals_for_per_unit_monthly_curve() -> None:
    calculator = StrategicIndicatorsCalculator()
    indicator = StrategicIndicatorCatalogItem(
        indicator_id="commercial-rol",
        department_id="commercial",
        indicator_name="ROL",
        weight_pct=40,
        goal_label="01: Curva R$ | 02: Curva R$",
        goal_value=3_466_000,
        goal_periodicity="monthly",
        goal_mode="monthly_curve",
        scope_type="per_unit",
        performance_direction="higher_is_better",
        value_unit="currency",
        value_decimals=2,
        branch_goals={
            "01": {
                "goal_label": "Curva R$",
                "goal_value": 0,
                "goal_periodicity": "monthly",
                "goal_mode": "monthly_curve",
                "monthly_targets": [{"month_number": 5, "target_value": 3_466_000}],
            },
            "02": {
                "goal_label": "Curva R$",
                "goal_value": 0,
                "goal_periodicity": "monthly",
                "goal_mode": "monthly_curve",
                "monthly_targets": [{"month_number": 5, "target_value": 1_006_000}],
            },
        },
    )

    calculated = calculator.calculate_indicators(
        indicators_catalog=[indicator],
        measurements=[
            StrategicIndicatorMeasuredValue(
                indicator_id="commercial-rol",
                department_id="commercial",
                value=1_908_690.84,
                source="commercial_rol",
                unit_values={"01": 614_974.68, "02": 3_202_406.99},
            )
        ],
        competence="2026-05",
        start_date="01-05-2026",
        end_date="27-05-2026",
    )

    assert len(calculated) == 1
    assert calculated[0].unit_goals == {"01": 3_466_000.0, "02": 1_006_000.0}

    goals_payload = calculator.resolve_goals_payload_for_calculated(
        calculated=calculated[0],
        catalog_item=indicator,
        start_date="01-05-2026",
        end_date="27-05-2026",
        competence="2026-05",
    )
    assert goals_payload == {"01": 3_466_000.0, "02": 1_006_000.0}

    stale = StrategicIndicatorCalculatedValue(
        indicator_id=calculated[0].indicator_id,
        department_id=calculated[0].department_id,
        indicator_name=calculated[0].indicator_name,
        weight_pct=calculated[0].weight_pct,
        goal_label=calculated[0].goal_label,
        goal_value=calculated[0].goal_value,
        goal_periodicity=calculated[0].goal_periodicity,
        goal_mode=calculated[0].goal_mode,
        monthly_targets=calculated[0].monthly_targets,
        scope_type=calculated[0].scope_type,
        performance_direction=calculated[0].performance_direction,
        strategic_description=calculated[0].strategic_description,
        source=calculated[0].source,
        value=calculated[0].value,
        score=calculated[0].score,
        gap=calculated[0].gap,
        unit_values=calculated[0].unit_values,
        unit_gaps=calculated[0].unit_gaps,
    )
    assert getattr(stale, "unit_goals", None) is None
    recomputed = calculator.resolve_goals_payload_for_calculated(
        calculated=stale,
        catalog_item=indicator,
        start_date="01-05-2026",
        end_date="27-05-2026",
        competence="2026-05",
    )
    assert recomputed == {"01": 3_466_000.0, "02": 1_006_000.0}


def test_resolve_unit_goals_ignores_stale_consolidated_cache() -> None:
    calculator = StrategicIndicatorsCalculator()
    indicator = StrategicIndicatorCatalogItem(
        indicator_id="commercial-rol",
        department_id="commercial",
        indicator_name="ROL",
        weight_pct=40,
        goal_label="01: Curva R$ | 02: Curva R$",
        goal_value=0,
        goal_periodicity="monthly",
        goal_mode="monthly_curve",
        scope_type="per_unit",
        performance_direction="higher_is_better",
        branch_goals={
            "01": {
                "goal_label": "Curva R$",
                "goal_value": 0,
                "goal_periodicity": "monthly",
                "goal_mode": "monthly_curve",
                "monthly_targets": [{"month_number": 5, "target_value": 3_466_000}],
            },
            "02": {
                "goal_label": "Curva R$",
                "goal_value": 0,
                "goal_periodicity": "monthly",
                "goal_mode": "monthly_curve",
                "monthly_targets": [{"month_number": 5, "target_value": 1_006_000}],
            },
        },
    )
    calculated = StrategicIndicatorCalculatedValue(
        indicator_id="commercial-rol",
        department_id="commercial",
        indicator_name="ROL",
        weight_pct=40,
        goal_label=indicator.goal_label,
        goal_value=0,
        goal_periodicity="monthly",
        goal_mode="monthly_curve",
        scope_type="per_unit",
        performance_direction="higher_is_better",
        value=1_000_000,
        unit_values={"01": 100.0, "02": 200.0},
        unit_goals={"consolidated": 0.0},
    )

    resolved = calculator.resolve_unit_goals_for_response(
        calculated=calculated,
        catalog_item=indicator,
        start_date="01-05-2026",
        end_date="31-05-2026",
        competence="2026-05",
    )

    assert resolved == {"01": 3_466_000.0, "02": 1_006_000.0}


def test_scope_branch_02_uses_filial_unit_value_and_goal() -> None:
    calculator = StrategicIndicatorsCalculator()
    indicator = StrategicIndicatorCatalogItem(
        indicator_id="hr-pdi",
        department_id="hr",
        indicator_name="PDIs ativos",
        weight_pct=10,
        goal_label="8 PDIs",
        goal_value=8.0,
        goal_periodicity="monthly",
        scope_type="consolidated",
        performance_direction="higher_is_better",
        branch_goals={},
        resolved_goal_scope_branch="02",
        has_resolved_goal=True,
    )

    calculated = calculator.calculate_indicators(
        indicators_catalog=[indicator],
        measurements=[
            StrategicIndicatorMeasuredValue(
                indicator_id="hr-pdi",
                department_id="hr",
                value=9.5,
                source="portal_rh_pdi_count",
                unit_values={"01": 10.0, "02": 5.0},
            )
        ],
        competence="2026-04",
        start_date="01-04-2026",
        end_date="30-04-2026",
        scope_branch="02",
    )

    assert len(calculated) == 1
    assert calculated[0].value == 5.0
    assert calculated[0].score is not None
    assert calculated[0].score < 8.0


def test_scope_branch_keeps_consolidated_value_when_no_branch_goal() -> None:
    calculator = StrategicIndicatorsCalculator()
    indicator = StrategicIndicatorCatalogItem(
        indicator_id="engineering-transforma",
        department_id="engineering",
        indicator_name="Ganhos TRANSFORMA+",
        weight_pct=40,
        goal_label="Sem meta para filial 01",
        goal_value=0.0,
        goal_periodicity="monthly",
        scope_type="consolidated",
        performance_direction="higher_is_better",
        branch_goals={},
        resolved_goal_scope_branch="",
        has_resolved_goal=False,
    )

    calculated = calculator.calculate_indicators(
        indicators_catalog=[indicator],
        measurements=[
            StrategicIndicatorMeasuredValue(
                indicator_id="engineering-transforma",
                department_id="engineering",
                value=14845.85,
                source="transforma",
                unit_values={"01": 6949.99, "02": 7895.86},
            )
        ],
        competence="2026-04",
        start_date="01-04-2026",
        end_date="30-04-2026",
        scope_branch="01",
    )

    assert len(calculated) == 1
    assert calculated[0].value == 14845.85
    assert calculated[0].score is None
    assert calculated[0].classification == calculator.MISSING_GOAL_CLASSIFICATION
    assert calculated[0].unit_values is None


def test_scope_branch_02_department_average_of_units_single_branch() -> None:
    calculator = StrategicIndicatorsCalculator()
    catalog = [
        StrategicIndicatorCatalogItem(
            indicator_id="hr-pdi",
            department_id="hr",
            indicator_name="PDIs",
            weight_pct=100,
            goal_label="8",
            goal_value=8.0,
            goal_periodicity="monthly",
            scope_type="consolidated",
            performance_direction="higher_is_better",
            branch_goals={},
            resolved_goal_scope_branch="02",
            has_resolved_goal=True,
        )
    ]
    measurements = [
        StrategicIndicatorMeasuredValue(
            indicator_id="hr-pdi",
            department_id="hr",
            value=9.5,
            source="test",
            unit_values={"01": 10.0, "02": 5.0},
        )
    ]

    departments = calculator.calculate_departments(
        departments_catalog=[
            StrategicDepartmentCatalogItem(
                department_id="hr",
                department_name="RH",
                short_name="RH",
                weight_pct=15,
                strategic_summary="",
                aggregation_mode="average_of_units",
            )
        ],
        indicators_catalog=catalog,
        measurements=measurements,
        competence="2026-04",
        start_date="01-04-2026",
        end_date="30-04-2026",
        scope_branch="02",
    )

    assert len(departments) == 1
    assert departments[0].score == 6.25


def test_branch_view_per_unit_goals_payload_uses_active_branch_key() -> None:
    calculator = StrategicIndicatorsCalculator()
    indicator = StrategicIndicatorCatalogItem(
        indicator_id="commercial-rol",
        department_id="commercial",
        indicator_name="ROL",
        weight_pct=40,
        goal_label="Meta",
        goal_value=0.0,
        goal_periodicity="monthly",
        goal_mode="monthly_curve",
        monthly_targets=[{"month_number": 5, "target_value": 1_006_000.0}],
        scope_type="per_unit",
        performance_direction="higher_is_better",
        branch_goals={
            "01": {
                "goal_label": "Meta",
                "goal_value": 1_006_000.0,
                "goal_periodicity": "monthly",
                "goal_mode": "monthly_curve",
                "monthly_targets": [{"month_number": 5, "target_value": 1_006_000.0}],
            },
            "02": {
                "goal_label": "Meta",
                "goal_value": 3_466_000.0,
                "goal_periodicity": "monthly",
                "goal_mode": "monthly_curve",
                "monthly_targets": [{"month_number": 5, "target_value": 3_466_000.0}],
            },
        },
        resolved_goal_scope_branch="01",
        has_resolved_goal=True,
        value_unit="currency",
    )
    measurement = StrategicIndicatorMeasuredValue(
        indicator_id="commercial-rol",
        department_id="commercial",
        value=651_977.42,
        source="commercial",
        unit_values={"01": 651_977.42, "02": 3_275_114.46},
    )

    calculated = calculator.calculate_indicators(
        indicators_catalog=[indicator],
        measurements=[measurement],
        competence="2026-05",
        start_date="01-05-2026",
        end_date="31-05-2026",
        scope_branch="01",
    )

    assert len(calculated) == 1
    item = calculated[0]
    assert item.unit_goals == {"01": 1_006_000.0}
    assert item.unit_gaps == {"01": 354_022.58}

    goals_payload = calculator.resolve_goals_payload_for_calculated(
        calculated=item,
        catalog_item=indicator,
        start_date="01-05-2026",
        end_date="31-05-2026",
        competence="2026-05",
    )

    assert goals_payload == {"01": 1_006_000.0}
    assert "consolidated" not in goals_payload
