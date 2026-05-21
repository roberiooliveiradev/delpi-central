from __future__ import annotations

from types import SimpleNamespace

from si_app.application.dto.strategic_indicators.catalog_models import (
    StrategicIndicatorCalculatedValue,
)
from si_app.infrastructure.providers.strategic_indicators.calculated_alerts_summary_provider import (
    CalculatedStrategicIndicatorsAlertsSummaryProvider,
)


def _department(*, indicators: list[StrategicIndicatorCalculatedValue]) -> SimpleNamespace:
    return SimpleNamespace(
        department_id="financial",
        department_name="Financeiro",
        score=7.5,
        contribution=1.5,
        classification="Satisfatório com Alertas",
        indicators=indicators,
    )


def test_indicator_risk_alert_ignores_indicators_without_score() -> None:
    provider = CalculatedStrategicIndicatorsAlertsSummaryProvider()

    alerts = provider.get_alerts_summary(
        departments=[
            _department(
                indicators=[
                    StrategicIndicatorCalculatedValue(
                        indicator_id="financial-fixed-cost",
                        department_id="financial",
                        indicator_name="Custos fixos",
                        weight_pct=30,
                        goal_label="Meta",
                        goal_value=14,
                        goal_periodicity="monthly",
                        value=None,
                        score=None,
                        gap=None,
                        classification="Sem dados preenchidos",
                    ),
                    StrategicIndicatorCalculatedValue(
                        indicator_id="financial-ebitda",
                        department_id="financial",
                        indicator_name="EBITDA",
                        weight_pct=30,
                        goal_label="Meta",
                        goal_value=12,
                        goal_periodicity="monthly",
                        value=10.0,
                        score=5.0,
                        gap=-2.0,
                        classification="Regular, Exige Ação",
                    ),
                ]
            )
        ],
        measurement_errors=[],
    )

    risk_titles = [item["title"] for item in alerts if "Risco concentrado" in item["title"]]
    assert len(risk_titles) == 1
