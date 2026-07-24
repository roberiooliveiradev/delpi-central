from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.application.services.response_meta_builder import DATA_VERSION
from app.application.services.strategic_indicators import dashboard_goal_source_keys as goal_keys


def _body(response) -> dict:
    return json.loads(response.content.decode())


@pytest.fixture
def quality_losses_client() -> TestClient:
    from fastapi import FastAPI

    from app.interface.http.routes.quality.quality_router import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_quality_losses_routes_exposed(quality_losses_client: TestClient) -> None:
    from app.interface.http.routes.quality.quality_router import router

    paths = {route.path for route in router.routes if hasattr(route, "path")}
    assert "/quality/scrap-cost-pct" in paths
    assert "/quality/rework-cost-pct" in paths


@patch(
    "app.interface.http.routes.quality.losses_routes.enrich_dashboard_metric",
    side_effect=lambda payload, **kwargs: {
        **payload,
        "has_goal": True,
        "comparable_goal": 0.6,
        "source_key": kwargs.get("source_key"),
    },
)
@patch(
    "app.interface.http.routes.quality.losses_routes.build_get_refugos_scrap_cost_pct_use_case"
)
def test_quality_scrap_cost_pct_returns_envelope(
    mock_builder, mock_enrich, quality_losses_client: TestClient
) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "branch": "01",
        "scrap_cost": 2500.0,
        "rol_with_ipi": 100_000.0,
        "scrap_cost_pct": 2.5,
    }
    mock_builder.return_value = use_case

    response = quality_losses_client.get(
        "/quality/scrap-cost-pct",
        params={"branch": "01", "date_start": "2026-06-01", "date_end": "2026-06-30"},
    )
    body = _body(response)

    assert response.status_code == 200
    assert body["success"] is True
    assert body["meta"]["operationId"] == "get_quality_scrap_cost_pct"
    assert body["meta"]["entity"] == "quality_scrap_cost_pct"
    assert body["meta"]["shape"] == "scalar"
    assert body["meta"]["dataVersion"] == DATA_VERSION
    assert body["data"]["scrap_cost_pct"] == 2.5
    assert body["data"]["comparable_goal"] == 0.6
    assert "scrap_cost_pct" in (body["meta"].get("fields") or {})
    mock_enrich.assert_called_once()
    assert mock_enrich.call_args.kwargs["source_key"] == goal_keys.QUALITY_SCRAP_COST_PCT


@patch(
    "app.interface.http.routes.quality.losses_routes.enrich_dashboard_metric",
    side_effect=lambda payload, **kwargs: payload,
)
@patch(
    "app.interface.http.routes.quality.losses_routes.build_get_refugos_scrap_cost_pct_use_case"
)
def test_quality_scrap_cost_pct_allows_omitted_branch(
    mock_builder, _mock_enrich, quality_losses_client: TestClient
) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "branch": "consolidated",
        "scrap_cost_pct": 1.0,
    }
    mock_builder.return_value = use_case

    response = quality_losses_client.get(
        "/quality/scrap-cost-pct",
        params={"date_start": "2026-06-01", "date_end": "2026-06-30"},
    )
    body = _body(response)

    assert response.status_code == 200
    assert body["meta"]["operationId"] == "get_quality_scrap_cost_pct"
    assert body["data"]["branch"] == "consolidated"


@patch(
    "app.interface.http.routes.quality.losses_routes.enrich_dashboard_metric",
    side_effect=lambda payload, **kwargs: {
        **payload,
        "has_goal": True,
        "comparable_goal": 0.1,
        "source_key": kwargs.get("source_key"),
    },
)
@patch(
    "app.interface.http.routes.quality.losses_routes.build_get_retrabalho_rework_cost_pct_use_case"
)
def test_quality_rework_cost_pct_returns_envelope(
    mock_builder, mock_enrich, quality_losses_client: TestClient
) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "branch": "01",
        "rework_cost": 500.0,
        "rol_with_ipi": 100_000.0,
        "rework_cost_pct": 0.5,
    }
    mock_builder.return_value = use_case

    response = quality_losses_client.get(
        "/quality/rework-cost-pct",
        params={"branch": "01", "date_start": "2026-06-01", "date_end": "2026-06-30"},
    )
    body = _body(response)

    assert response.status_code == 200
    assert body["meta"]["operationId"] == "get_quality_rework_cost_pct"
    assert body["meta"]["entity"] == "quality_rework_cost_pct"
    assert body["meta"]["shape"] == "scalar"
    assert body["data"]["rework_cost_pct"] == 0.5
    assert body["data"]["comparable_goal"] == 0.1
    assert "rework_cost_pct" in (body["meta"].get("fields") or {})
    assert mock_enrich.call_args.kwargs["source_key"] == goal_keys.QUALITY_REWORK_COST_PCT
