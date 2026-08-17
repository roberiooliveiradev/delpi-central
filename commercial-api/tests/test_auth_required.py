from fastapi.testclient import TestClient

from commercial_app.main import app


def test_protected_route_requires_token():
    client = TestClient(app)
    response = client.get("/seller-portfolios/me")
    assert response.status_code == 401
    payload = response.json()
    assert payload.get("detail") == "Unauthorized"
