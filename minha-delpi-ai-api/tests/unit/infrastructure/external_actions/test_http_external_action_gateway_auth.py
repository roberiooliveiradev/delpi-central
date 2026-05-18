from app.infrastructure.external_actions.http_external_action_gateway import (
    HttpExternalActionGateway,
)


def test_build_headers_forwards_user_token():
    gateway = HttpExternalActionGateway()

    headers = gateway._build_headers(
        {"authMode": "user_token", "authConfig": {}},
        "user-jwt-token",
    )

    assert headers["Authorization"] == "Bearer user-jwt-token"


def test_build_headers_forwards_forward_user_bearer_alias():
    gateway = HttpExternalActionGateway()

    headers = gateway._build_headers(
        {"authMode": "forward_user_bearer", "authConfig": {}},
        "user-jwt-token",
    )

    assert headers["Authorization"] == "Bearer user-jwt-token"


def test_build_headers_api_key_bearer():
    gateway = HttpExternalActionGateway()

    headers = gateway._build_headers(
        {
            "authMode": "api_key",
            "authConfig": {
                "apiKey": "secret",
                "headerName": "Authorization",
                "scheme": "bearer",
            },
        },
        None,
    )

    assert headers["Authorization"] == "Bearer secret"
