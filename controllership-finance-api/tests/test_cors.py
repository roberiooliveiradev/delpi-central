from fastapi.testclient import TestClient

from controllership_finance_app.main import app


def test_allowed_origin_receives_cors_header():
    client = TestClient(app)
    response = client.get("/health", headers={"Origin": "http://localhost"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost"


def test_unknown_origin_receives_no_cors_header():
    client = TestClient(app)
    response = client.get("/health", headers={"Origin": "https://evil.example.com"})
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_no_origin_request_has_no_cors_header():
    client = TestClient(app)
    response = client.get("/health")
    assert "access-control-allow-origin" not in response.headers


def test_preflight_allowed_origin_and_method_succeeds():
    client = TestClient(app)
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost"


def test_preflight_disallowed_origin_is_rejected():
    client = TestClient(app)
    response = client.options(
        "/health",
        headers={
            "Origin": "https://evil.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
