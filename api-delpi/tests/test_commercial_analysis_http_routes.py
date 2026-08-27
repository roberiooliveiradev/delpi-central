"""Smoke HTTP — rotas consolidadas comerciais (group_by + meta)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _authenticated_superadmin_http():
    user = MagicMock()
    user.id = "11111111-1111-4111-8111-111111111111"
    user.is_superadmin = True
    with patch("delpi_auth.authorization.resolve_user_context", return_value=user):
        yield user


@pytest.fixture()
def commercial_client() -> TestClient:
    from fastapi import FastAPI

    from app.interface.http.routes.commercial.commercial_router import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


@patch("app.interface.http.routes.commercial.commercial_router.enrich_dashboard_metric", side_effect=lambda payload, **_: payload)
@patch("app.interface.http.routes.commercial.commercial_router.build_get_commercial_rol_analysis_use_case")
def test_http_commercial_rol_group_by_customer(mock_build, _mock_enrich, commercial_client: TestClient) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "summary": {
            "start_date": "2024-08-01",
            "end_date": "2024-08-31",
            "totals": {"rol": 100.0},
            "by_branch": {"branch_01": {"rol": 50.0}, "branch_02": {"rol": 50.0}},
        },
        "series": [{"period_label": "sem 1", "rol_filial_01": 50.0, "rol_filial_02": 50.0}],
        "by_customer": [
            {"customer_name": "Cliente A", "branch": "01", "rol": 10.0, "rank": 1}
        ],
        "granularity": "week",
        "group_by": "customer",
        "pagination": {"page": 1, "page_size": 50, "total": 1, "has_more": False},
    }
    mock_build.return_value = use_case

    response = commercial_client.get(
        "/commercial/rol",
        params={
            "start_date": "2024-08-01",
            "end_date": "2024-08-31",
            "granularity": "week",
            "group_by": "customer",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["operationId"] == "get_commercial_rol"
    assert payload["meta"]["shape"] == "composite_analysis"
    assert payload["data"]["by_customer"][0]["customer_name"] == "Cliente A"
    assert "rol" in payload["meta"]["fields"]
    assert payload["meta"]["fields"]["rol"] == "ROL realizado"


@patch("app.interface.http.routes.commercial.commercial_router.enrich_dashboard_metric", side_effect=lambda payload, **_: payload)
@patch("app.interface.http.routes.commercial.commercial_router.build_get_commercial_rol_analysis_use_case")
def test_http_commercial_rol_group_by_branch(mock_build, _mock_enrich, commercial_client: TestClient) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "summary": {
            "start_date": "2024-08-01",
            "end_date": "2024-08-31",
            "totals": {"rol": 100.0},
            "by_branch": {"branch_01": {"rol": 40.0}, "branch_02": {"rol": 60.0}},
        },
        "series": [],
        "by_customer": [],
        "by_branch": [
            {"branch": "01", "rol": 40.0},
            {"branch": "02", "rol": 60.0},
        ],
        "granularity": "week",
        "group_by": "branch",
    }
    mock_build.return_value = use_case

    response = commercial_client.get(
        "/commercial/rol",
        params={
            "start_date": "2024-08-01",
            "end_date": "2024-08-31",
            "group_by": "branch",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["by_branch"][0]["branch"] == "01"


@patch("app.interface.http.routes.commercial.commercial_router.enrich_dashboard_metric", side_effect=lambda payload, **_: payload)
@patch("app.interface.http.routes.commercial.commercial_router.build_get_commercial_sales_order_otd_analysis_use_case")
def test_http_otd_analysis_group_by_customer(mock_build, _mock_enrich, commercial_client: TestClient) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "summary": {
            "start_date": "2026-08-03",
            "end_date": "2026-08-07",
            "totals": {"otd_pct": 90.0, "total_qty": 100.0},
            "by_branch": {"branch_01": {"otd_pct": 90.0}, "branch_02": {"otd_pct": 88.0}},
        },
        "series": [],
        "by_customer": [{"customer_name": "Weg", "branch": "01", "otd_pct": 100.0}],
        "granularity": "week",
        "group_by": "customer",
        "pagination": {"page": 1, "page_size": 50, "total": 1, "has_more": False},
    }
    mock_build.return_value = use_case

    response = commercial_client.get(
        "/commercial/sales-order-otd/analysis",
        params={
            "start_date": "2026-08-03",
            "end_date": "2026-08-07",
            "group_by": "customer",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["operationId"] == "get_commercial_sales_order_otd_analysis"
    assert payload["data"]["by_customer"][0]["customer_name"] == "Weg"


def test_http_commercial_rol_rejects_invalid_group_by(commercial_client: TestClient) -> None:
    response = commercial_client.get(
        "/commercial/rol",
        params={"group_by": "product"},
    )
    assert response.status_code == 422
