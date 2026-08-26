from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx

from delpi_api_client.client import DelpiApiClient


def test_get_accepts_scalar_query_param() -> None:
    client = DelpiApiClient(base_url="http://example.test", caller_app="test-app")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"success": True, "data": {"ok": True}}
    with patch("delpi_api_client.client.httpx.Client") as client_cls:
        instance = client_cls.return_value.__enter__.return_value
        instance.get.return_value = mock_response
        client.get_path("/demo", params={"branch": "01", "ignored": None})
        _, kwargs = instance.get.call_args
        assert kwargs["params"] == {"branch": "01"}


def test_get_accepts_list_query_param() -> None:
    client = DelpiApiClient(base_url="http://example.test", caller_app="test-app")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"success": True, "data": {"ok": True}}
    with patch("delpi_api_client.client.httpx.Client") as client_cls:
        instance = client_cls.return_value.__enter__.return_value
        instance.get.return_value = mock_response
        client.get_path(
            "/supplies/purchase-requests/lines",
            params={"cost_centers": ["0413", "0520"], "branch": "01"},
        )
        _, kwargs = instance.get.call_args
        assert kwargs["params"]["branch"] == "01"
        assert kwargs["params"]["cost_centers"] == ["0413", "0520"]


def test_get_preserves_special_characters_in_scalar_values() -> None:
    client = DelpiApiClient(base_url="http://example.test", caller_app="test-app")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"success": True, "data": {}}
    with patch("delpi_api_client.client.httpx.Client") as client_cls:
        instance = client_cls.return_value.__enter__.return_value
        instance.get.return_value = mock_response
        client.get_path("/demo", params={"request_number": "SC-100/A"})
        _, kwargs = instance.get.call_args
        assert kwargs["params"]["request_number"] == "SC-100/A"
