from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.application.services.strategic_indicators.dashboard_si_indicator_metric_service import (
    DashboardSiIndicatorMetricService,
)
from app.interface.http.route_contract_registry import resolve_contract
from tests.support.si_indicator_tv_operation_ids import SI_INDICATOR_TV_OPERATION_IDS


def test_si_indicator_catalog_operation_ids_inventory() -> None:
    assert len(SI_INDICATOR_TV_OPERATION_IDS) == 64
    assert "get_si_indicator_quality_ppm_internal_realized" in SI_INDICATOR_TV_OPERATION_IDS
    assert "get_si_indicator_quality_ppm_internal_meta" in SI_INDICATOR_TV_OPERATION_IDS
    assert "get_si_indicator_quality_ppm_external_realized" in SI_INDICATOR_TV_OPERATION_IDS
    assert "get_si_indicator_quality_ppm_external_meta" in SI_INDICATOR_TV_OPERATION_IDS


def test_resolve_contract_si_indicator_families() -> None:
    entity, shape = resolve_contract("get_si_indicator_quality_ppm_internal_realized")
    assert entity == "dashboard_si_indicator_realized"
    assert shape == "scalar"
    entity, shape = resolve_contract("get_si_indicator_quality_ppm_internal_meta")
    assert entity == "dashboard_si_indicator_meta"
    assert shape == "scalar"


def test_get_metric_realized_returns_payload() -> None:
    mock_client = MagicMock()
    mock_client.get_dashboard_indicator_realized.return_value = {
        "indicator_id": "quality-ppm-internal",
        "value": 12.5,
        "has_value": True,
    }
    service = DashboardSiIndicatorMetricService(client=mock_client)

    result = service.get_metric(
        indicator_id="quality-ppm-internal",
        kind="realized",
        start_date="2026-06-01",
        end_date="2026-06-30",
        branch="1",
    )

    assert result["value"] == 12.5
    mock_client.get_dashboard_indicator_realized.assert_called_once_with(
        indicator_id="quality-ppm-internal",
        competence=None,
        start_date="01-06-2026",
        end_date="30-06-2026",
        branch="01",
    )


def test_get_metric_meta_returns_payload() -> None:
    mock_client = MagicMock()
    mock_client.get_dashboard_indicator_meta.return_value = {
        "indicator_id": "quality-ppm-internal",
        "value": 10.0,
        "comparable_goal": 10.0,
    }
    service = DashboardSiIndicatorMetricService(client=mock_client)

    result = service.get_metric(
        indicator_id="quality-ppm-internal",
        kind="meta",
        competence="2026-06",
    )

    assert result["comparable_goal"] == 10.0
    mock_client.get_dashboard_indicator_meta.assert_called_once()


def test_si_indicator_realized_route_meta() -> None:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.interface.http.routes.dashboard.dashboard_router import router
    from tests.support.route_contract_smoke import assert_envelope_meta

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    with patch(
        "app.interface.http.routes.dashboard.dashboard_router."
        "get_dashboard_si_indicator_metric_service"
    ) as mock_svc:
        mock_svc.return_value.get_metric.return_value = {
            "indicator_id": "quality-ppm-internal",
            "name": "PPM Interno",
            "value": 12.0,
            "has_value": True,
        }
        response = client.get(
            "/dashboard/indicators/quality-ppm-internal/realized",
            params={"competence": "2026-06"},
        )

    assert response.status_code == 200
    assert_envelope_meta(
        response.json(),
        operation_id="get_si_indicator_quality_ppm_internal_realized",
        shape="scalar",
        entity="dashboard_si_indicator_realized",
    )
    assert response.json()["data"]["value"] == 12.0


def test_si_indicator_meta_route_meta() -> None:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.interface.http.routes.dashboard.dashboard_router import router
    from tests.support.route_contract_smoke import assert_envelope_meta

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    with patch(
        "app.interface.http.routes.dashboard.dashboard_router."
        "get_dashboard_si_indicator_metric_service"
    ) as mock_svc:
        mock_svc.return_value.get_metric.return_value = {
            "indicator_id": "quality-ppm-internal",
            "name": "PPM Interno",
            "value": 10.0,
            "comparable_goal": 10.0,
            "has_value": True,
        }
        response = client.get(
            "/dashboard/indicators/quality-ppm-internal/meta",
            params={"competence": "2026-06"},
        )

    assert response.status_code == 200
    assert_envelope_meta(
        response.json(),
        operation_id="get_si_indicator_quality_ppm_internal_meta",
        shape="scalar",
        entity="dashboard_si_indicator_meta",
    )


def test_si_indicator_route_404_when_missing() -> None:
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
        mock_svc.return_value.get_metric.return_value = None
        response = client.get("/dashboard/indicators/quality-ppm-internal/realized")

    assert response.status_code == 404
