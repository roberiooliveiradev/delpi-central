from __future__ import annotations

from si_app.application.services.strategic_indicators.measurements_cache_policy import (
    MISSING_DEPARTMENT_ERROR_CODE,
)
from si_app.infrastructure.providers.strategic_indicators.calculated_alerts_summary_provider import (
    CalculatedStrategicIndicatorsAlertsSummaryProvider,
)


def test_measurement_error_alert_lists_missing_departments() -> None:
    provider = CalculatedStrategicIndicatorsAlertsSummaryProvider()
    errors = [
        {
            "department_id": "commercial",
            "source": "commercial_snapshot",
            "message": "HTTP 504 gateway timeout",
            "code": "measurement_fetch_error",
        },
        {
            "department_id": "production",
            "source": "si_measurements_quality",
            "message": "Nenhuma medição foi retornada para Produção.",
            "code": MISSING_DEPARTMENT_ERROR_CODE,
        },
    ]

    alerts = provider.get_alerts_summary(
        departments=[],
        measurement_errors=errors,
    )

    fetch_alerts = [
        item
        for item in alerts
        if "coleta" in item["title"].lower() or "fontes" in item["title"].lower()
    ]
    assert fetch_alerts
    alert = fetch_alerts[0]
    assert "HTTP 504" in alert["impact"]
    assert "Produção" in alert["impact"]
