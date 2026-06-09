import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))

from delpi_api_client.client import DelpiApiClient  # noqa: E402


def test_get_sends_caller_app_header() -> None:
    with patch("delpi_api_client.client.httpx.Client") as mock_client_cls:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"success": True, "data": {"total": 0}}

        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        client = DelpiApiClient(
            base_url="http://test-api",
            caller_app="strategic-indicators-api",
        )
        client.get_stock_value()

        _args, kwargs = mock_client.get.call_args
        assert kwargs["headers"]["X-Delpi-Caller-App"] == "strategic-indicators-api"
