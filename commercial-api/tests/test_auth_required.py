from fastapi.testclient import TestClient

from commercial_app.main import app


def test_protected_route_requires_token():
    client = TestClient(app)
    response = client.get("/seller-portfolios/me")
    assert response.status_code == 401
    payload = response.json()
    assert payload.get("detail") == "Unauthorized"


def test_new_bff_routes_require_token():
    client = TestClient(app)
    for path in (
        "/settings/sla-policies",
        "/analytics/opportunity-collaborator-summary",
        "/interaction-rooms/00000000-0000-0000-0000-000000000001",
    ):
        response = client.get(path)
        assert response.status_code == 401, path
        assert response.json().get("detail") == "Unauthorized"


def test_interaction_room_resolve_requires_token():
    client = TestClient(app)
    response = client.post(
        "/interaction-rooms/resolve",
        json={"kind": "entity", "entity_type": "order", "entity_key": "01|1"},
    )
    assert response.status_code == 401
    assert response.json().get("detail") == "Unauthorized"


def test_declared_forecast_route_removed():
    paths = {getattr(route, "path", "") for route in app.routes}
    assert "/forecast/current" not in paths
    assert not any(str(path).startswith("/forecast") for path in paths)
