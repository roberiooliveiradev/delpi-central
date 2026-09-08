def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "ok"
    assert body["service"] == "supplies-api"


def test_ready_returns_ok(client):
    response = client.get("/ready")
    assert response.status_code == 200
    body = response.get_json()
    assert body["ready"] is True
    assert body["service"] == "supplies-api"
