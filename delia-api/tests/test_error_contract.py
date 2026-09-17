def test_unknown_route_does_not_leak_environment(client, monkeypatch):
    monkeypatch.setenv("SECRET_TOKEN", "must-not-appear")
    response = client.get("/not-a-real-route")
    assert response.status_code == 404
    body = response.get_json()
    assert body["code"] == "not_found"
    assert "must-not-appear" not in response.get_data(as_text=True)
    assert "SECRET_TOKEN" not in response.get_data(as_text=True)


def test_health_does_not_echo_headers(client):
    response = client.get(
        "/health",
        headers={"Authorization": "Bearer secret-token", "X-Request-Id": "req-1"},
    )
    assert response.status_code == 200
    text = response.get_data(as_text=True)
    assert "secret-token" not in text
    assert "Bearer" not in text
    assert response.headers.get("X-Request-Id") == "req-1"
