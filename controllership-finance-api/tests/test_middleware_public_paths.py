from fastapi.testclient import TestClient

from controllership_finance_app.main import app


def test_health_is_public_without_token():
    client = TestClient(app)
    assert client.get("/health").status_code == 200


def test_ready_is_public_without_token():
    client = TestClient(app)
    assert client.get("/ready").status_code == 200


def test_unknown_route_does_not_bypass_auth():
    client = TestClient(app)
    response = client.get("/internal/anything")
    assert response.status_code == 401


def test_health_under_root_path_prefix_is_public():
    client = TestClient(app, root_path="/apps/controllership-finance-api")
    response = client.get("/apps/controllership-finance-api/health")
    assert response.status_code == 200
    assert response.json()["service"] == "controllership-finance-api"
