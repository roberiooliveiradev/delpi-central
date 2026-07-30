from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx

from cec_app.infrastructure.gateways.core_directory_service import (
    CecCoreDirectoryService,
)


def test_lookup_emails_by_user_ids_maps_valid_items():
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "items": [
            {"id": "u1", "name": "A", "email": "a@delpi.com.br"},
            {"id": "u2", "name": "B", "email": "invalid"},
            {"id": "u3", "name": "C", "email": "c@delpi.com.br"},
        ]
    }
    with patch(
        "cec_app.infrastructure.gateways.core_directory_service.httpx.post",
        return_value=response,
    ) as post:
        svc = CecCoreDirectoryService(
            core_api_url="http://core-api:8000",
            service_token="tok",
        )
        result = svc.lookup_emails_by_user_ids(["u1", "u2", "u3"])

    assert result == {"u1": "a@delpi.com.br", "u3": "c@delpi.com.br"}
    assert post.call_args.kwargs["json"] == {"ids": ["u1", "u2", "u3"]}


def test_lookup_returns_empty_without_token():
    svc = CecCoreDirectoryService(core_api_url="http://core-api:8000", service_token="")
    assert svc.lookup_emails_by_user_ids(["u1"]) == {}
