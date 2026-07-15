from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.application.services.response_meta_builder import DATA_VERSION


def _body(response) -> dict:
    return json.loads(response.content.decode())


@pytest.fixture
def pa_client() -> TestClient:
    from fastapi import FastAPI

    from app.interface.http.routes.production_appointments.production_appointments_router import (
        router,
    )

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_router_exposes_all_endpoints(pa_client: TestClient) -> None:
    from app.interface.http.routes.production_appointments.production_appointments_router import (
        router,
    )

    paths = {route.path for route in router.routes if hasattr(route, "path")}
    assert router.prefix == "/production/appointments"
    assert "/production/appointments/work-centers" in paths
    assert "/production/appointments" in paths
    assert "/production/appointments/summary" in paths
    assert "/production/appointments/series" in paths
    assert "/production/appointments/by-op" in paths


def test_summary_requires_branch(pa_client: TestClient) -> None:
    response = pa_client.get("/production/appointments/summary")
    assert response.status_code == 422


@patch(
    "app.interface.http.routes.production_appointments.production_appointments_router.branch_access_error",
    return_value=None,
)
@patch(
    "app.interface.http.routes.production_appointments.production_appointments_router.build_get_production_appointments_summary_use_case"
)
def test_summary_returns_playbook_meta(
    mock_builder, _mock_branch, pa_client: TestClient
) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "totals": {"qty_produced": 10.5},
        "items": [],
    }
    mock_builder.return_value = use_case

    response = pa_client.get(
        "/production/appointments/summary",
        params={"branch": "01", "date_start": "2026-06-15", "date_end": "2026-07-15"},
    )
    body = _body(response)

    assert response.status_code == 200
    assert body["success"] is True
    assert body["meta"]["operationId"] == "get_production_appointments_summary"
    assert body["meta"]["entity"] == "production_appointments_summary"
    assert body["meta"]["shape"] == "playbook_report"
    assert body["meta"]["dataVersion"] == DATA_VERSION
    assert body["data"]["totals"]["qty_produced"] == 10.5


@patch(
    "app.interface.http.routes.production_appointments.production_appointments_router.branch_access_error",
    return_value=None,
)
@patch(
    "app.interface.http.routes.production_appointments.production_appointments_router.build_list_production_appointments_use_case"
)
def test_list_returns_paged_list_meta(
    mock_builder, _mock_branch, pa_client: TestClient
) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {"items": [], "pagination": {"total": 0}}
    mock_builder.return_value = use_case

    response = pa_client.get(
        "/production/appointments",
        params={"branch": "01"},
    )
    body = _body(response)

    assert response.status_code == 200
    assert body["meta"]["operationId"] == "list_production_appointments"
    assert body["meta"]["shape"] == "paged_list"
