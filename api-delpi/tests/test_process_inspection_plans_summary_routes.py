"""Smoke HTTP — process inspection plans summary."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


def _body(response) -> dict:
    return json.loads(response.body.decode())


@patch(
    "app.interface.http.routes.process_inspection_plans.process_inspection_plans_router.branch_access_error",
    return_value=None,
)
@patch(
    "app.interface.http.routes.process_inspection_plans.process_inspection_plans_router.build_get_process_inspection_plans_summary_use_case"
)
def test_process_inspection_plans_summary_returns_meta(mock_build, _mock_branch) -> None:
    from app.interface.http.routes.process_inspection_plans.process_inspection_plans_router import (
        get_process_inspection_plans_summary_route,
    )

    mock_result = MagicMock()
    mock_result.to_dict.return_value = {
        "branch": "01",
        "products_without_plan": 39,
        "orders_without_plan": 63,
        "total_open_orders": 448,
        "orders_with_plan": 385,
        "registered_pct": 85.94,
                        "distribution": [
                            {"status": "with_plan", "label": "Com inspeção", "count": 385, "pct": 85.94},
                            {"status": "without_plan", "label": "Sem inspeção", "count": 63, "pct": 14.06},
                        ],
    }
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = mock_result
    mock_build.return_value = mock_use_case

    response = get_process_inspection_plans_summary_route(branch="01")
    body = _body(response)

    assert body.get("success") is True
    meta = body.get("meta")
    assert isinstance(meta, dict)
    assert meta.get("operationId") == "get_process_inspection_plans_summary"
    assert meta.get("shape") == "scalar"
    assert meta.get("entity") == "process_inspection_plans_summary"
    assert body.get("data", {}).get("branch") == "01"


@pytest.fixture
def process_inspection_plans_client() -> TestClient:
    from fastapi import FastAPI

    from app.interface.http.routes.process_inspection_plans.process_inspection_plans_router import (
        router,
    )

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


@patch(
    "app.interface.http.routes.process_inspection_plans.process_inspection_plans_router.branch_access_error",
    return_value=None,
)
@patch(
    "app.interface.http.routes.process_inspection_plans.process_inspection_plans_router.build_get_process_inspection_plans_summary_use_case"
)
def test_process_inspection_plans_summary_allows_omit_branch(
    mock_build, _access, process_inspection_plans_client: TestClient
) -> None:
    mock_result = MagicMock()
    mock_result.to_dict.return_value = {"branch": "all", "total_open_orders": 0}
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = mock_result
    mock_build.return_value = mock_use_case

    response = process_inspection_plans_client.get("/process-inspection-plans/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["operationId"] == "get_process_inspection_plans_summary"
