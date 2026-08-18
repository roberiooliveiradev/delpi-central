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
        "/forecast/current",
        "/settings/sla-policies",
        "/analytics/opportunity-collaborator-summary",
    ):
        response = client.get(path)
        assert response.status_code == 401, path
        assert response.json().get("detail") == "Unauthorized"
