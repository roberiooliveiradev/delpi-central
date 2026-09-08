def test_request_id_generated(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("X-Request-Id")


def test_request_id_propagated(client):
    response = client.get("/health", headers={"X-Request-Id": "req-fixed-1"})
    assert response.headers.get("X-Request-Id") == "req-fixed-1"
