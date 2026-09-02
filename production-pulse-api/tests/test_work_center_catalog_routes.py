from unittest.mock import MagicMock, patch


def _create_device(client, unique_ip: str, name: str = "ESP teste"):
    response = client.post(
        "/devices",
        json={
            "name": name,
            "branch": "01",
            "ipAddress": unique_ip,
            "driverKey": "esp8266_counter_v1",
        },
    )
    assert response.status_code == 201
    return response.json()["data"]


@patch(
    "production_pulse_app.interface.http.routes.catalog_routes._catalog_service",
    autospec=True,
)
def test_catalog_work_centers_route(mock_service, client):
    mock_service.list_work_centers.return_value = {
        "branch": "01",
        "items": [
            {
                "branch": "01",
                "workCenterCode": "CT-53",
                "workCenterName": "Usinagem CNC",
                "isFinalInspection": False,
            }
        ],
        "summary": {"totalRecords": 1, "branchFilterApplied": True},
    }

    response = client.get("/catalog/work-centers", params={"branch": "01", "search": "CT"})
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["items"][0]["workCenterCode"] == "CT-53"
    mock_service.list_work_centers.assert_called_once()


def test_binding_rejects_unknown_work_center(client, unique_ip, monkeypatch):
    device = _create_device(client, unique_ip, "ESP posto")

    mock_catalog = MagicMock()
    from production_pulse_app.domain.services.binding_validation_service import (
        BindingValidationError,
    )

    mock_catalog.validate_work_center_code.side_effect = BindingValidationError(
        "work_center_not_in_catalog",
        work_center_code="CT-404",
    )

    monkeypatch.setattr(
        "production_pulse_app.interface.http.routes.device_routes._binding_service._work_centers",
        mock_catalog,
    )

    response = client.put(
        f"/devices/{device['id']}/binding",
        json={
            "anchorType": "work_center",
            "workCenterCode": "CT-404",
            "workCenterName": "Inexistente",
        },
    )
    assert response.status_code == 422
    assert "não existe no catálogo" in response.json()["error"]["message"]


def test_binding_accepts_known_work_center(client, unique_ip, monkeypatch):
    device = _create_device(client, unique_ip, "ESP posto CT")

    mock_catalog = MagicMock()
    mock_catalog.validate_work_center_code.return_value = None

    monkeypatch.setattr(
        "production_pulse_app.interface.http.routes.device_routes._binding_service._work_centers",
        mock_catalog,
    )

    response = client.put(
        f"/devices/{device['id']}/binding",
        json={
            "anchorType": "work_center",
            "workCenterCode": "CT-53",
            "workCenterName": "Usinagem CNC",
        },
    )
    assert response.status_code == 200
    binding = response.json()["data"]
    assert binding["workCenterCode"] == "CT-53"
    assert binding["placementKey"] == "wc:01:CT-53"
    mock_catalog.validate_work_center_code.assert_called_once()
