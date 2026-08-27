from __future__ import annotations

from unittest.mock import MagicMock, patch

from cipa_app.infrastructure.gateways.core_directory_service import CipaCoreDirectoryService


def test_directory_lookup_maps_items_and_uses_integrations_token():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "items": [
            {"id": "u1", "email": "a@delpi.com.br"},
            {"id": "u2", "email": "invalid"},
        ]
    }
    with patch(
        "cipa_app.infrastructure.gateways.core_directory_service.httpx.post",
        return_value=mock_response,
    ) as post:
        svc = CipaCoreDirectoryService(
            core_api_url="http://core-api:8000",
            service_token="integrations-token",
        )
        assert svc.lookup_emails_by_user_ids(["u1", "u2"]) == {"u1": "a@delpi.com.br"}

    post.assert_called_once()
    headers = post.call_args.kwargs["headers"]
    assert headers["Authorization"] == "Bearer integrations-token"
    assert headers["X-Delpi-Service-Token"] == "integrations-token"


def test_directory_lookup_returns_empty_when_not_configured():
    svc = CipaCoreDirectoryService(core_api_url="", service_token="")
    assert svc.lookup_emails_by_user_ids(["u1"]) == {}
