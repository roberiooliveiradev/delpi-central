from fastapi.testclient import TestClient

from production_pulse_app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["service"] == "production-pulse-api"
    assert body["data"]["status"] == "ok"
