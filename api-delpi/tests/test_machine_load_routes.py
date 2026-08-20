"""Smoke — /production/machine-load."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.application.services.response_meta_builder import DATA_VERSION


def _body(response) -> dict:
    return json.loads(response.content.decode())


@pytest.fixture
def machine_load_client() -> TestClient:
    from fastapi import FastAPI

    from app.interface.http.routes.production.machine_load_router import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_router_exposes_work_centers_and_operations() -> None:
    from app.interface.http.routes.production.machine_load_router import router

    paths = {route.path for route in router.routes if hasattr(route, "path")}
    assert router.prefix == "/production/machine-load"
    assert "/production/machine-load/work-centers" in paths
    assert "/production/machine-load/operations" in paths
    assert "/production/machine-load/appointment-status" in paths


@patch(
    "app.interface.http.routes.production.machine_load_router"
    ".build_get_production_machine_load_work_centers_use_case"
)
def test_work_centers_returns_list_envelope(
    mock_builder, machine_load_client: TestClient
) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "filters": {"scheduled_start": "2026-08-19", "scheduled_end": "2026-08-26"},
        "items": [
            {
                "work_center": "CT-02",
                "work_center_name": "APLICAÇÃO DE TERMINAIS",
                "operation_count": 42,
                "order_count": 21,
            }
        ],
        "summary": {"work_center_count": 1, "operation_count": 42},
    }
    mock_builder.return_value = use_case

    response = machine_load_client.get(
        "/production/machine-load/work-centers",
        params={"branch": "01"},
    )
    assert response.status_code == 200
    payload = _body(response)
    assert payload["success"] is True
    assert payload["meta"]["operationId"] == "get_production_machine_load_work_centers"
    assert payload["meta"]["entity"] == "production_machine_load_work_centers"
    assert payload["meta"]["shape"] == "list"
    assert payload["meta"]["dataVersion"] == DATA_VERSION
    assert payload["data"]["items"][0]["work_center"] == "CT-02"


@patch(
    "app.interface.http.routes.production.machine_load_router"
    ".build_get_production_machine_load_operations_use_case"
)
def test_operations_returns_paged_list_envelope(
    mock_builder, machine_load_client: TestClient
) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "filters": {"work_center": "CT-02"},
        "items": [
            {
                "work_center": "CT-02",
                "scheduled_date": "2026-08-20",
                "production_order": "24640401002",
                "operation_description": "CORTAR E APLICAR",
                "tool": "23-B31",
                "product_code": "50320064",
                "planned_qty": 7.1,
                "pa_due_date": "2026-08-21",
            }
        ],
        "pagination": {
            "page": 1,
            "page_size": 100,
            "total": 1,
            "total_pages": 1,
            "is_complete": True,
        },
    }
    mock_builder.return_value = use_case

    response = machine_load_client.get(
        "/production/machine-load/operations",
        params={"branch": "01", "work_center": "CT-02"},
    )
    assert response.status_code == 200
    payload = _body(response)
    assert payload["meta"]["operationId"] == "get_production_machine_load_operations"
    assert payload["meta"]["entity"] == "production_machine_load_operations"
    assert payload["meta"]["shape"] == "paged_list"
    assert payload["data"]["items"][0]["production_order"] == "24640401002"


def test_invalid_window_returns_400(machine_load_client: TestClient) -> None:
    response = machine_load_client.get(
        "/production/machine-load/operations",
        params={
            "branch": "01",
            "scheduled_start": "2026-08-26",
            "scheduled_end": "2026-08-19",
        },
    )
    assert response.status_code == 400
    assert _body(response)["success"] is False


def test_invalid_sort_is_rejected_by_query_pattern(
    machine_load_client: TestClient,
) -> None:
    response = machine_load_client.get(
        "/production/machine-load/operations",
        params={"branch": "01", "sort": "bogus"},
    )
    assert response.status_code == 422


@patch(
    "app.interface.http.routes.production.machine_load_router"
    ".build_get_production_machine_load_appointment_status_use_case"
)
def test_appointment_status_returns_list_envelope(
    mock_builder, machine_load_client: TestClient
) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "branch": "02",
        "items": [
            {
                "production_order": "10808301002",
                "operation_code": "01",
                "production_status": "in_progress",
                "is_in_production": True,
                "active_operator_name": "SILVANA ANDRADE DOS SANTOS",
            }
        ],
        "summary": {"requested_count": 1, "in_production_count": 1},
    }
    mock_builder.return_value = use_case

    response = machine_load_client.post(
        "/production/machine-load/appointment-status",
        json={
            "branch": "02",
            "items": [{"production_order": "10808301002", "operation_code": "01"}],
        },
    )
    assert response.status_code == 200
    payload = _body(response)
    assert payload["meta"]["operationId"] == (
        "get_production_machine_load_appointment_status"
    )
    assert payload["meta"]["entity"] == "production_machine_load_appointment_status"
    assert payload["data"]["items"][0]["is_in_production"] is True
