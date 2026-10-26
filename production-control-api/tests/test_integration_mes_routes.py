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
        self.last_downtimes_kwargs = kwargs
        return {
            "branch": kwargs["branch"], "referenceAt": "2026-09-29T13:00:00+00:00",
            "page": kwargs["page"], "pageSize": kwargs["page_size"], "total": 0, "items": [],
        }

    def list_downtime_sources(self):
        return {"items": [{"code": "system"}, {"code": "operator_pause"}]}

    def get_downtime_analytics(self, **kwargs):
        self.last_analytics_kwargs = kwargs
        return {
            "branch": kwargs["branch"], "from": "2026-09-22T03:00:00+00:00",
            "to": "2026-09-29T03:00:00+00:00",
            "referenceAt": "2026-09-29T13:00:00+00:00",
            "timezone": "America/Sao_Paulo",
            "appliedFilters": {},
            "summary": {"totalStoppedSeconds": 0, "attributedSeconds": 0,
                        "occurrencesCount": 0, "averageOccurrenceSeconds": 0,
                        "pendingCount": 0, "openCount": 0},
            "byReason": [], "byWorkCenter": [], "byDay": [],
            "byWeekdayHour": [],
            "quality": {"overlapDetected": False, "overlapSeconds": 0,
                        "partial": False, "factsCapped": False},
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


def test_downtime_management_filters_reach_the_service(monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "internal-secret")
    service = FakeService()
    app = FastAPI()
    app.include_router(integration_mes_routes.router)
    monkeypatch.setattr(integration_mes_routes, "build_mes_integration_read_service", lambda: service)
    api = TestClient(app)
    response = api.get(
        "/integrations/mes/downtimes?branch=01&workCenter=CT-35"
        "&reasonCode=setup&source=system&classification=pending&sort=oldest"
        "&downtimeId=9f2a1b3c-1234-4abc-9def-000000000001&page=1&pageSize=10",
        headers={"X-Delpi-Service-Token": "internal-secret"},
    )
    assert response.status_code == 200
    kwargs = service.last_downtimes_kwargs
    assert kwargs["reason_code"] == "setup"
    assert kwargs["source"] == "system"
    assert kwargs["classification"] == "pending"
    assert kwargs["sort"] == "oldest"
    assert kwargs["downtime_id"] == "9f2a1b3c-1234-4abc-9def-000000000001"


def test_downtime_sources_requires_service_token_and_returns_items(monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "internal-secret")
    api = client(monkeypatch)
    assert api.get("/integrations/mes/downtime-sources").status_code == 401
    response = api.get(
        "/integrations/mes/downtime-sources",
        headers={"X-Delpi-Service-Token": "internal-secret"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["items"] == [{"code": "system"}, {"code": "operator_pause"}]


def test_integration_path_bypasses_human_jwt_middleware_only_for_route_guard():
    from production_control_app.middleware.auth_middleware import _is_internal_integration

    assert _is_internal_integration("/integrations/mes/work-centers/live") is True
    assert _is_internal_integration("/apps/production-control-api/integrations/mes/downtimes") is True
    assert _is_internal_integration("/machine-load") is False


def test_downtime_analytics_requires_service_token(monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "internal-secret")
    api = client(monkeypatch)
    response = api.get(
        "/integrations/mes/downtimes/analytics"
        "?branch=01&from=2026-09-22T03:00:00Z"
    )
    assert response.status_code == 401


def test_downtime_analytics_requires_from_param(monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "internal-secret")
    api = client(monkeypatch)
    response = api.get(
        "/integrations/mes/downtimes/analytics?branch=01",
        headers={"X-Delpi-Service-Token": "internal-secret"},
    )
    assert response.status_code == 422


def test_downtime_analytics_filters_reach_the_service(monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "internal-secret")
    service = FakeService()
    app = FastAPI()
    app.include_router(integration_mes_routes.router)
    monkeypatch.setattr(integration_mes_routes, "build_mes_integration_read_service", lambda: service)
    api = TestClient(app)
    response = api.get(
        "/integrations/mes/downtimes/analytics?branch=01"
        "&from=2026-09-22T03:00:00%2B00:00&to=2026-09-29T03:00:00%2B00:00"
        "&workCenter=CT-35&reasonCode=setup&source=system"
        "&classification=pending",
        headers={"X-Delpi-Service-Token": "internal-secret"},
    )
    assert response.status_code == 200
    kwargs = service.last_analytics_kwargs
    assert kwargs["branch"] == "01"
    assert kwargs["work_center"] == "CT-35"
    assert kwargs["reason_code"] == "setup"
    assert kwargs["source"] == "system"
    assert kwargs["classification"] == "pending"
    assert "page" not in kwargs and "sort" not in kwargs
    assert "downtime_id" not in kwargs
