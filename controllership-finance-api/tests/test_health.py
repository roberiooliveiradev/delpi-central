from fastapi.testclient import TestClient

from controllership_finance_app.main import app


def test_root_health():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "online"
    assert payload["service"] == "controllership-finance-api"


def test_ready_reports_config_state(monkeypatch):
    from controllership_finance_app.config import settings
    from controllership_finance_app.interface.http.routes import health_routes

    monkeypatch.setattr(
        health_routes,
        "missing_required_config",
        lambda: [],
    )
    client = TestClient(app)
    response = client.get("/ready")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["service"] == "controllership-finance-api"
    assert payload["config_ready"] is True
    assert "core_hint" not in payload


def test_ready_degraded_when_config_missing(monkeypatch):
    from controllership_finance_app.interface.http.routes import health_routes

    monkeypatch.setattr(
        health_routes,
        "missing_required_config",
        lambda: ["KEYCLOAK_ISSUER", "CORE_API_INTEGRATIONS_SERVICE_TOKEN"],
    )
    client = TestClient(app)
    response = client.get("/ready")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "degraded"
    assert payload["config_ready"] is False
    assert "KEYCLOAK_ISSUER" in payload["core_hint"]


def test_ready_never_exposes_secret_values(monkeypatch):
    from controllership_finance_app.interface.http.routes import health_routes

    monkeypatch.setattr(
        health_routes,
        "missing_required_config",
        lambda: ["CORE_API_INTEGRATIONS_SERVICE_TOKEN"],
    )
    client = TestClient(app)
    response = client.get("/ready")
    body = response.text
    assert "Bearer" not in body
    assert "token=" not in body.lower()


def test_openapi_has_literal_operation_ids():
    client = TestClient(app)
    spec = client.get("/openapi.json").json()
    operation_ids = {
        path_item["get"]["operationId"]
        for path, path_item in spec["paths"].items()
        if "get" in path_item
    }
    assert "get_controllership_finance_health" in operation_ids
    assert "get_controllership_finance_ready" in operation_ids
    assert len(operation_ids) == len(set(operation_ids))
