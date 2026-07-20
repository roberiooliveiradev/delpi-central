from __future__ import annotations

from unittest.mock import MagicMock

from app.application.services.strategic_indicators.dashboard_department_indicators_service import (
    DashboardDepartmentIndicatorsService,
)


def test_get_department_indicators_returns_item_from_client() -> None:
    mock_client = MagicMock()
    mock_client.get_dashboard_department_indicators.return_value = {
        "item": {
            "department_id": "commercial",
            "idd": 8.1,
            "indicators": [
                {
                    "indicator_id": "commercial.otd",
                    "goals": {"consolidated": 95.0},
                    "realized": {"consolidated": 92.0},
                }
            ],
        }
    }
    service = DashboardDepartmentIndicatorsService(client=mock_client)

    result = service.get_department_indicators(
        department_id="commercial",
        start_date="2026-06-01",
        end_date="2026-06-30",
        branch="1",
    )

    assert result["department_id"] == "commercial"
    assert result["idd"] == 8.1
    assert result["indicators"][0]["goals"]["consolidated"] == 95.0
    mock_client.get_dashboard_department_indicators.assert_called_once_with(
        department_id="commercial",
        competence=None,
        start_date="01-06-2026",
        end_date="30-06-2026",
        branch="01",
    )


def test_list_departments_indicators_returns_items() -> None:
    mock_client = MagicMock()
    mock_client.list_dashboard_departments_indicators.return_value = {
        "items": [{"department_id": "quality", "idd": 7.0, "indicators": []}],
        "partial_success": False,
        "errors": [],
    }
    service = DashboardDepartmentIndicatorsService(client=mock_client)

    result = service.list_departments_indicators(competence="2026-06")

    assert len(result["items"]) == 1
    assert result["items"][0]["idd"] == 7.0
    mock_client.list_dashboard_departments_indicators.assert_called_once_with(
        competence="2026-06",
        start_date=None,
        end_date=None,
        branch=None,
        department_id=None,
    )


def test_get_dashboard_department_indicators_route_meta() -> None:
    from unittest.mock import patch

    from app.interface.http.routes.dashboard.dashboard_router import (
        get_dashboard_department_indicators,
    )
    from tests.support.route_contract_smoke import assert_envelope_meta, body_json

    with patch(
        "app.interface.http.routes.dashboard.dashboard_router."
        "get_dashboard_department_indicators_service"
    ) as mock_svc:
        mock_svc.return_value.get_department_indicators.return_value = {
            "department_id": "quality",
            "idd": 7.5,
            "indicators": [],
        }
        response = get_dashboard_department_indicators(
            department_id="quality",
            competence="2026-06",
            start_date=None,
            end_date=None,
            branch=None,
        )

    assert_envelope_meta(
        body_json(response),
        operation_id="get_dashboard_department_indicators",
        shape="playbook_report",
        entity="dashboard_department_indicators",
    )


def test_get_dashboard_departments_indicators_route_meta() -> None:
    from unittest.mock import patch

    from app.interface.http.routes.dashboard.dashboard_router import (
        get_dashboard_departments_indicators,
    )
    from tests.support.route_contract_smoke import assert_envelope_meta, body_json

    with patch(
        "app.interface.http.routes.dashboard.dashboard_router."
        "get_dashboard_department_indicators_service"
    ) as mock_svc:
        mock_svc.return_value.list_departments_indicators.return_value = {
            "items": [],
            "partial_success": False,
            "errors": [],
        }
        response = get_dashboard_departments_indicators(
            competence=None,
            start_date=None,
            end_date=None,
            branch=None,
            department_id=None,
        )

    assert_envelope_meta(
        body_json(response),
        operation_id="get_dashboard_departments_indicators",
        shape="playbook_report",
        entity="dashboard_departments_indicators",
    )


def test_dashboard_department_id_rejects_invalid_value_with_422() -> None:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.interface.http.routes.dashboard.dashboard_router import router

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    response = client.get(
        "/dashboard/department-indicators",
        params={"department_id": "marketing"},
    )
    assert response.status_code == 422
