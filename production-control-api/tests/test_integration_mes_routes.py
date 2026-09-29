from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from production_control_app.interface.http.routes import integration_mes_routes


class FakeService:
    def get_live_work_centers(self, *, branch):
        return {"branch": branch, "referenceAt": "2026-09-29T13:00:00+00:00", "summary": {}, "items": []}

    def get_run_timeline(self, run_id):
        return {"runId": run_id, "referenceAt": "2026-09-29T13:00:00+00:00", "summary": {}, "items": []}

    def get_work_center_timeline(self, **kwargs):
        return {
            "branch": kwargs["branch"], "workCenter": kwargs["work_center"],
            "from": kwargs["period_from"].isoformat(), "to": "2026-09-29T13:00:00+00:00",
            "referenceAt": "2026-09-29T13:00:00+00:00", "items": [],
        }

    def list_downtimes(self, **kwargs):
        return {
            "branch": kwargs["branch"], "referenceAt": "2026-09-29T13:00:00+00:00",
            "page": kwargs["page"], "pageSize": kwargs["page_size"], "total": 0, "items": [],
        }


def client(monkeypatch):
    app = FastAPI()
    app.include_router(integration_mes_routes.router)
    monkeypatch.setattr(integration_mes_routes, "build_mes_integration_read_service", lambda: FakeService())
    return TestClient(app)


def test_missing_service_token_is_rejected(monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "internal-secret")
    response = client(monkeypatch).get("/integrations/mes/work-centers/live?branch=01")
    assert response.status_code == 401


def test_invalid_service_token_is_rejected(monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "internal-secret")
    response = client(monkeypatch).get(
        "/integrations/mes/work-centers/live?branch=01",
        headers={"X-Delpi-Service-Token": "wrong"},
    )
    assert response.status_code == 401


def test_human_jwt_without_service_token_is_rejected(monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "internal-secret")
    response = client(monkeypatch).get(
        "/integrations/mes/work-centers/live?branch=01",
        headers={"Authorization": "Bearer human-jwt"},
    )
    assert response.status_code == 401


def test_valid_service_token_allows_all_read_contracts(monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "internal-secret")
    headers = {
        "X-Delpi-Service-Token": "internal-secret",
        "X-Delpi-Caller-App": "delpi-mes-api",
    }
    api = client(monkeypatch)
    responses = [
        api.get("/integrations/mes/work-centers/live?branch=01", headers=headers),
        api.get("/integrations/mes/runs/run-1/timeline", headers=headers),
        api.get("/integrations/mes/downtimes?branch=01&page=1&pageSize=50", headers=headers),
        api.get(
            "/integrations/mes/work-centers/CT-35/timeline?branch=01&from=2026-09-29T00:00:00%2B00:00",
            headers=headers,
        ),
    ]
    assert [response.status_code for response in responses] == [200, 200, 200, 200]
    assert all(response.json()["success"] is True for response in responses)
    assert "internal-secret" not in str([response.json() for response in responses])


def test_work_center_timeline_requires_service_token(monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "internal-secret")
    response = client(monkeypatch).get(
        "/integrations/mes/work-centers/CT-35/timeline?branch=01&from=2026-09-29T00:00:00%2B00:00"
    )
    assert response.status_code == 401


def test_bearer_service_token_is_supported(monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "internal-secret")
    response = client(monkeypatch).get(
        "/integrations/mes/work-centers/live?branch=01",
        headers={"Authorization": "Bearer internal-secret"},
    )
    assert response.status_code == 200


def test_integration_path_bypasses_human_jwt_middleware_only_for_route_guard():
    from production_control_app.middleware.auth_middleware import _is_internal_integration

    assert _is_internal_integration("/integrations/mes/work-centers/live") is True
    assert _is_internal_integration("/apps/production-control-api/integrations/mes/downtimes") is True
    assert _is_internal_integration("/machine-load") is False
