import responses

from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGateway, DelpiApiGatewayError
import pytest


@responses.activate
def test_get_forwards_caller_and_bearer(monkeypatch):
    monkeypatch.delenv("API_DELPI_INTERNAL_SERVICE_TOKEN", raising=False)
    responses.add(
        responses.GET,
        "http://delpi-api.test/supplies/otd",
        json={"ok": True},
        status=200,
    )
    gateway = DelpiApiGateway(
        base_url="http://delpi-api.test",
        timeout_seconds=2.0,
        caller_app="supplies-api",
    )
    data = gateway.get("/supplies/otd", access_token="tok-1")
    assert data == {"ok": True}
    assert responses.calls[0].request.headers["Authorization"] == "Bearer tok-1"
    assert responses.calls[0].request.headers["X-Delpi-Caller-App"] == "supplies-api"
    assert "X-Delpi-Service-Token" not in responses.calls[0].request.headers


@responses.activate
def test_get_adds_service_token_without_replacing_user_bearer(monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "svc-secret")
    responses.add(
        responses.GET,
        "http://delpi-api.test/supplies/purchase-orders",
        json={"ok": True},
        status=200,
    )
    gateway = DelpiApiGateway(
        base_url="http://delpi-api.test",
        timeout_seconds=2.0,
        caller_app="supplies-api",
    )
    gateway.get("/supplies/purchase-orders", access_token="user-tok")
    headers = responses.calls[0].request.headers
    assert headers["Authorization"] == "Bearer user-tok"
    assert headers["X-Delpi-Caller-App"] == "supplies-api"
    assert headers["X-Delpi-Service-Token"] == "svc-secret"


@responses.activate
def test_get_timeout_raises():
    responses.add(
        responses.GET,
        "http://delpi-api.test/slow",
        body=responses.ConnectionError(),
    )
    gateway = DelpiApiGateway(base_url="http://delpi-api.test", timeout_seconds=1.0)
    with pytest.raises(DelpiApiGatewayError):
        gateway.get("/slow", access_token="tok")
