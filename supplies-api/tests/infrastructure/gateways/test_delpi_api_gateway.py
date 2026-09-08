import responses

from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGateway, DelpiApiGatewayError
import pytest


@responses.activate
def test_get_forwards_caller_and_bearer():
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
