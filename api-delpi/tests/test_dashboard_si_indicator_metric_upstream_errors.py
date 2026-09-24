from __future__ import annotations

import pytest
from strategic_indicators_client import StrategicIndicatorsApiError

from app.application.services.strategic_indicators.si_client_error_policy import (
    is_si_not_found_error,
)


def test_is_si_not_found_error_positive_variants() -> None:
    assert is_si_not_found_error(
        StrategicIndicatorsApiError(
            "Strategic Indicators API retornou 404: "
            '{"detail":"Indicador \'x\' não encontrado no SI."}'
        )
    )
    assert is_si_not_found_error(
        StrategicIndicatorsApiError("Indicador 'x' não encontrado no SI.")
    )
    assert is_si_not_found_error(StrategicIndicatorsApiError("[404] not found"))


def test_is_si_not_found_error_negative_timeout_and_500() -> None:
    assert not is_si_not_found_error(
        StrategicIndicatorsApiError(
            "Falha de rede ao consultar Strategic Indicators API: timed out"
        )
    )
    assert not is_si_not_found_error(
        StrategicIndicatorsApiError(
            "Strategic Indicators API retornou 500: "
            '{"detail":"Falha ao resolver realized do indicador SI: '
            "duplicate key value violates unique constraint "
            '\\"uq_si_period_scores_scope_version\\"}'
        )
    )


def test_get_metric_caches_true_404_as_none() -> None:
    from unittest.mock import MagicMock

    from app.application.services.strategic_indicators.dashboard_si_indicator_metric_service import (
        DashboardSiIndicatorMetricService,
    )

    mock_client = MagicMock()
    mock_client.get_dashboard_indicator_realized.side_effect = (
        StrategicIndicatorsApiError(
            "Strategic Indicators API retornou 404: "
            '{"detail":"Indicador \'quality-kaizen-financial\' não encontrado no SI."}'
        )
    )
    service = DashboardSiIndicatorMetricService(client=mock_client)

    first = service.get_metric(
        indicator_id="quality-kaizen-financial",
        kind="realized",
        start_date="2026-09-01",
        end_date="2026-09-30",
        branch="01",
    )
    second = service.get_metric(
        indicator_id="quality-kaizen-financial",
        kind="realized",
        start_date="2026-09-01",
        end_date="2026-09-30",
        branch="01",
    )

    assert first is None
    assert second is None
    assert mock_client.get_dashboard_indicator_realized.call_count == 1


def test_get_metric_reraises_upstream_500_without_caching() -> None:
    from unittest.mock import MagicMock

    from app.application.services.strategic_indicators.dashboard_si_indicator_metric_service import (
        DashboardSiIndicatorMetricService,
    )

    mock_client = MagicMock()
    mock_client.get_dashboard_indicator_realized.side_effect = (
        StrategicIndicatorsApiError(
            "Strategic Indicators API retornou 500: "
            '{"detail":"duplicate key value violates unique constraint '
            '\\"uq_si_period_scores_scope_version\\"}'
        )
    )
    service = DashboardSiIndicatorMetricService(client=mock_client)

    with pytest.raises(StrategicIndicatorsApiError):
        service.get_metric(
            indicator_id="quality-kaizen-financial",
            kind="realized",
            start_date="2026-09-01",
            end_date="2026-09-30",
            branch="01",
        )

    # Sibling call must hit SI again (no poisoned negative cache).
    with pytest.raises(StrategicIndicatorsApiError):
        service.get_metric(
            indicator_id="quality-kaizen-financial",
            kind="realized",
            start_date="2026-09-01",
            end_date="2026-09-30",
            branch="01",
        )

    assert mock_client.get_dashboard_indicator_realized.call_count == 2


def test_si_indicator_route_503_on_upstream_failure() -> None:
    from unittest.mock import patch

    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.interface.http.routes.dashboard.dashboard_router import router

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    with patch(
        "app.interface.http.routes.dashboard.dashboard_router."
        "get_dashboard_si_indicator_metric_service"
    ) as mock_svc:
        mock_svc.return_value.get_metric.side_effect = StrategicIndicatorsApiError(
            "Strategic Indicators API retornou 500: boom"
        )
        response = client.get(
            "/dashboard/indicators/quality-kaizen-financial/realized",
            params={
                "start_date": "2026-09-01",
                "end_date": "2026-09-30",
                "branch": "01",
            },
        )

    assert response.status_code == 503
    assert "temporariamente indisponível" in response.json()["detail"]
