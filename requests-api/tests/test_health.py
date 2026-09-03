from fastapi.testclient import TestClient

from requests_app.main import app


def test_root_health():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "online"
    assert payload["service"] == "requests-api"
