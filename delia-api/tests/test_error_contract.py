from app.application.platform_access import PlatformAccessContext
from app.create_app import create_app


def test_unknown_route_without_auth_fails_closed():
    response = create_app(testing=True).test_client().get("/not-a-real-route")
    assert response.status_code == 401
    assert response.get_json()["code"] == "unauthenticated"


def test_unknown_route_authenticated_does_not_leak_environment(monkeypatch):
    monkeypatch.setenv("SECRET_TOKEN", "must-not-appear")

    class FakeProvider:
        def resolve(self, bearer_token: str) -> PlatformAccessContext:
            return PlatformAccessContext(
                user_id="u1",
                name="N",
                email="u@example.com",
                effective_permissions=("p1",),
            )

    app = create_app(testing=True, platform_access_provider=FakeProvider())
    response = app.test_client().get(
        "/not-a-real-route",
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 404
    body = response.get_json()
    assert body["code"] == "not_found"
    text = response.get_data(as_text=True)
    assert "must-not-appear" not in text
    assert "SECRET_TOKEN" not in text
    assert "test-token" not in text


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
