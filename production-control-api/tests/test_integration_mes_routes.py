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

    def export_downtimes(self, **kwargs):
        self.last_export_kwargs = kwargs
        return {
            "branch": kwargs["branch"],
            "referenceAt": "2026-09-29T13:00:00+00:00",
            "timezone": "America/Sao_Paulo",
            "appliedFilters": {},
            "total": 0, "capped": False, "items": [],
        }

    def get_downtime_insights(self, **kwargs):
        self.last_insights_kwargs = kwargs
        return {
            "branch": kwargs["branch"],
            "from": kwargs["period_from"].isoformat(),
            "to": "2026-09-29T13:00:00+00:00",
            "referenceAt": "2026-09-29T13:00:00+00:00",
            "timezone": "America/Sao_Paulo",
            "appliedFilters": {},
            "comparison": {"criteria": "immediately-preceding equal-duration window"},
            "recurrence": [], "critical": {"rules": {}, "items": []},
            "pendencies": {"unclassifiedCount": 0,
                           "openTreatmentsCount": 0, "openStopsCount": 0},
            "actionEffectiveness": [],
            "quality": {"telemetryGaps": []},
        }

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


def test_downtime_export_requires_service_token(monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "internal-secret")
    api = client(monkeypatch)
    assert api.get("/integrations/mes/downtimes/export?branch=01").status_code == 401


def test_downtime_export_filters_reach_the_service(monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "internal-secret")
    service = FakeService()
    app = FastAPI()
    app.include_router(integration_mes_routes.router)
    monkeypatch.setattr(integration_mes_routes, "build_mes_integration_read_service", lambda: service)
    api = TestClient(app)
    response = api.get(
        "/integrations/mes/downtimes/export?branch=01&workCenter=CT-35"
        "&status=open&pendency=true",
        headers={"X-Delpi-Service-Token": "internal-secret"},
    )
    assert response.status_code == 200
    kwargs = service.last_export_kwargs
    assert kwargs["branch"] == "01"
    assert kwargs["work_center"] == "CT-35"
    assert kwargs["status"] == "open"
    assert kwargs["pendency"] is True
    body = response.json()
    assert body["data"]["total"] == 0


def test_downtime_insights_requires_service_token(monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "internal-secret")
    api = client(monkeypatch)
    assert (
        api.get(
            "/integrations/mes/downtimes/insights?branch=01"
            "&from=2026-09-22T00:00:00Z"
        ).status_code
        == 401
    )


def test_downtime_insights_filters_reach_the_service(monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "internal-secret")
    service = FakeService()
    app = FastAPI()
    app.include_router(integration_mes_routes.router)
    monkeypatch.setattr(integration_mes_routes, "build_mes_integration_read_service", lambda: service)
    api = TestClient(app)
    response = api.get(
        "/integrations/mes/downtimes/insights?branch=01"
        "&from=2026-09-22T00:00:00Z&workCenter=CT-35&status=open",
        headers={"X-Delpi-Service-Token": "internal-secret"},
    )
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["comparison"]["criteria"] == (
        "immediately-preceding equal-duration window"
    )
    assert service.last_insights_kwargs["work_center"] == "CT-35"
    assert service.last_insights_kwargs["status"] == "open"


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


class FakeClassificationService:
    def __init__(self):
        self.last = None

    def classify_managed(self, downtime_id, **kwargs):
        self.last = (downtime_id, kwargs)
        return {
            "id": downtime_id,
            "reasonCode": kwargs["reason_code"],
            "confirmed": True,
            "confirmedByType": "manager",
            "updatedAt": "2026-09-29T13:00:00+00:00",
        }


class FakeTreatmentService:
    def __init__(self):
        self.calls = []

    def get_treatment(self, downtime_id, *, branch):
        self.calls.append(("get", downtime_id, branch))
        return None

    def upsert_treatment(self, downtime_id, **kwargs):
        self.calls.append(("upsert", downtime_id, kwargs))
        return {
            "downtimeId": downtime_id,
            "status": "pending",
            "analysis": kwargs["analysis"],
            "causeKind": kwargs["cause_kind"],
            "causeNote": kwargs.get("cause_note"),
            "actionNeeded": kwargs["action_needed"],
            "justification": kwargs["justification"],
            "requestRef": None,
            "updatedAt": "2026-09-29T13:00:00+00:00",
        }

    def link_request(self, downtime_id, **kwargs):
        self.calls.append(("link", downtime_id, kwargs))
        return {"downtimeId": downtime_id, "status": "referred",
                "requestRef": {"requestId": kwargs["request_id"],
                               "typeCode": kwargs["request_type_code"]}}

    def conclude(self, downtime_id, **kwargs):
        self.calls.append(("conclude", downtime_id, kwargs))
        return {"downtimeId": downtime_id, "status": "concluded"}

    def history(self, downtime_id, *, branch):
        self.calls.append(("history", downtime_id, branch))
        return [{"id": "a1", "action": "downtime_classified",
                 "actorType": "manager", "actorRef": "u1",
                 "occurredAt": "2026-09-29T13:00:00+00:00", "details": {}}]


def _headers():
    return {
        "X-Delpi-Service-Token": "internal-secret",
        "X-Delpi-Caller-App": "delpi-mes-api",
    }


def _write_client(monkeypatch, classification=None, treatment=None):
    app = FastAPI()
    app.include_router(integration_mes_routes.router)
    monkeypatch.setattr(
        integration_mes_routes,
        "build_mes_downtime_classification_service",
        lambda *a, **k: classification or FakeClassificationService(),
    )
    monkeypatch.setattr(
        integration_mes_routes,
        "build_mes_downtime_treatment_service",
        lambda: treatment or FakeTreatmentService(),
    )
    return TestClient(app)


_DT = "9f2a1b3c-1234-4abc-9def-000000000001"


def test_classify_requires_service_token(monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "internal-secret")
    api = _write_client(monkeypatch)
    response = api.post(
        f"/integrations/mes/downtimes/{_DT}/classification",
        json={
            "branch": "01", "reasonCode": "setup",
            "expectedUpdatedAt": "2026-09-29T13:00:00+00:00",
            "actorRef": "u1", "actorName": "Gestora",
        },
    )
    assert response.status_code == 401


def test_classify_forwards_payload_and_actor(monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "internal-secret")
    service = FakeClassificationService()
    api = _write_client(monkeypatch, classification=service)
    response = api.post(
        f"/integrations/mes/downtimes/{_DT}/classification",
        headers=_headers(),
        json={
            "branch": "01", "reasonCode": "setup", "note": "troca",
            "expectedUpdatedAt": "2026-09-29T13:00:00+00:00",
            "actorRef": "u1", "actorName": "Gestora",
        },
    )
    assert response.status_code == 200
    downtime_id, kwargs = service.last
    assert downtime_id == _DT
    assert kwargs["branch"] == "01"
    assert kwargs["reason_code"] == "setup"
    assert kwargs["actor_ref"] == "u1"
    assert kwargs["expected_updated_at"].tzinfo is not None


def test_classify_conflict_maps_to_409(monkeypatch):
    from production_control_app.domain.errors import DowntimeConflict

    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "internal-secret")

    class Conflicting(FakeClassificationService):
        def classify_managed(self, downtime_id, **kwargs):
            raise DowntimeConflict("stale")

    api = _write_client(monkeypatch, classification=Conflicting())
    response = api.post(
        f"/integrations/mes/downtimes/{_DT}/classification",
        headers=_headers(),
        json={
            "branch": "01", "reasonCode": "setup",
            "expectedUpdatedAt": "2026-09-29T13:00:00+00:00",
            "actorRef": "u1", "actorName": "G",
        },
    )
    assert response.status_code == 409


def test_classify_not_found_maps_to_404(monkeypatch):
    from production_control_app.domain.errors import DowntimeNotFound

    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "internal-secret")

    class Missing(FakeClassificationService):
        def classify_managed(self, downtime_id, **kwargs):
            raise DowntimeNotFound("nope")

    api = _write_client(monkeypatch, classification=Missing())
    response = api.post(
        f"/integrations/mes/downtimes/{_DT}/classification",
        headers=_headers(),
        json={
            "branch": "01", "reasonCode": "setup",
            "expectedUpdatedAt": "2026-09-29T13:00:00+00:00",
            "actorRef": "u1", "actorName": "G",
        },
    )
    assert response.status_code == 404


def test_treatment_roundtrip_routes(monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "internal-secret")
    api = _write_client(monkeypatch)
    upsert = api.put(
        f"/integrations/mes/downtimes/{_DT}/treatment",
        headers=_headers(),
        json={
            "branch": "01", "analysis": "recorrente", "causeKind": "hypothesis",
            "actionNeeded": True, "justification": "impacto",
            "actorRef": "u1", "actorName": "G",
        },
    )
    assert upsert.status_code == 200
    assert upsert.json()["data"]["status"] == "pending"

    link = api.post(
        f"/integrations/mes/downtimes/{_DT}/treatment/request-link",
        headers=_headers(),
        json={
            "branch": "01", "requestId": "9f2a1b3c-1234-4abc-9def-0000000000ff",
            "requestTypeCode": "process-issue", "actorRef": "u1",
            "actorName": "G",
        },
    )
    assert link.status_code == 200
    assert link.json()["data"]["status"] == "referred"

    conclude = api.post(
        f"/integrations/mes/downtimes/{_DT}/treatment/conclusion",
        headers=_headers(),
        json={
            "branch": "01", "reason": "atendida",
            "linkedRequestCompleted": True, "actorRef": "u1", "actorName": "G",
        },
    )
    assert conclude.status_code == 200
    assert conclude.json()["data"]["status"] == "concluded"

    history = api.get(
        f"/integrations/mes/downtimes/{_DT}/history?branch=01",
        headers=_headers(),
    )
    assert history.status_code == 200
    assert history.json()["data"]["items"][0]["action"] == "downtime_classified"


def test_treatment_routes_reject_without_token(monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "internal-secret")
    api = _write_client(monkeypatch)
    assert api.get(f"/integrations/mes/downtimes/{_DT}/treatment?branch=01").status_code == 401
    assert api.get(f"/integrations/mes/downtimes/{_DT}/history?branch=01").status_code == 401
