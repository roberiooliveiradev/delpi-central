from unittest.mock import MagicMock, patch

import requests

from app.infrastructure.external_actions.http_external_action_gateway import (
    HttpExternalActionGateway,
)


def _provider():
    return {
        "baseUrl": "http://api-delpi:8000",
        "authMode": "user_token",
    }


def _action(path="/products/{code}/factory-status"):
    return {
        "method": "GET",
        "path": path,
        "parametersSchema": [
            {"name": "code", "in": "path"},
        ],
    }


def test_execute_uses_composite_timeout_for_factory_status():
    gateway = HttpExternalActionGateway()
    response = MagicMock()
    response.status_code = 200
    response.headers = {"content-type": "application/json"}
    response.json.return_value = {"success": True, "data": {}}

    with patch("app.infrastructure.external_actions.http_external_action_gateway.requests.request") as request_mock:
        request_mock.return_value = response

        gateway.execute(
            provider=_provider(),
            action=_action(),
            parameters={"code": "90260140"},
            body=None,
            access_token="token",
            action_path="/products/{code}/factory-status",
        )

    assert request_mock.call_args.kwargs["timeout"] == 60


def test_execute_retries_once_on_503_then_succeeds():
    gateway = HttpExternalActionGateway()
    failure = MagicMock()
    failure.status_code = 503
    failure.headers = {"content-type": "application/json"}
    failure.json.return_value = {"success": False}

    success = MagicMock()
    success.status_code = 200
    success.headers = {"content-type": "application/json"}
    success.json.return_value = {"success": True, "data": {"items": []}}

    with patch("app.infrastructure.external_actions.http_external_action_gateway.requests.request") as request_mock:
        request_mock.side_effect = [failure, success]

        result = gateway.execute(
            provider=_provider(),
            action=_action(path="/production/schedule/today"),
            parameters={},
            body=None,
            access_token="token",
            action_path="/production/schedule/today",
        )

    assert request_mock.call_count == 2
    assert result["ok"] is True
    assert result["statusCode"] == 200


def test_execute_returns_timeout_payload_after_retry_exhausted():
    gateway = HttpExternalActionGateway()

    with patch("app.infrastructure.external_actions.http_external_action_gateway.requests.request") as request_mock:
        request_mock.side_effect = requests.Timeout()

        result = gateway.execute(
            provider=_provider(),
            action=_action(),
            parameters={"code": "90260140"},
            body=None,
            access_token="token",
            action_path="/products/{code}/factory-status",
        )

    assert request_mock.call_count == 2
    assert result["ok"] is False
    assert result["statusCode"] == 504
