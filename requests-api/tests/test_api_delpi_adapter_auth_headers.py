"""Adapter Authorization must be Bearer-prefixed for api-delpi JWT middleware."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from requests_app.application.errors import ApplicationError
from requests_app.infrastructure.gateways.api_delpi_adapter import (
    ApiDelpiAdapter,
    _as_bearer_authorization,
)


def test_as_bearer_authorization_prefixes_raw_jwt() -> None:
    assert _as_bearer_authorization("raw.jwt.token") == "Bearer raw.jwt.token"
    assert _as_bearer_authorization("Bearer already") == "Bearer already"
    assert _as_bearer_authorization(None) is None
    assert _as_bearer_authorization("  ") is None


def test_adapter_sends_bearer_authorization_header() -> None:
    adapter = ApiDelpiAdapter(base_url="http://api-delpi.test")
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {"data": {"items": []}}

    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = False
    mock_client.get.return_value = response

    with patch(
        "requests_app.infrastructure.gateways.api_delpi_adapter.httpx.Client",
        return_value=mock_client,
    ):
        adapter.search_parties(
            party_type="customer",
            query="weg",
            authorization="raw.jwt.token",
        )

    headers = mock_client.get.call_args.kwargs["headers"]
    assert headers["Authorization"] == "Bearer raw.jwt.token"


def test_adapter_maps_upstream_401_to_application_error() -> None:
    adapter = ApiDelpiAdapter(base_url="http://api-delpi.test")
    request = httpx.Request("GET", "http://api-delpi.test/request-lookups/parties")
    response = httpx.Response(401, request=request)

    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = False
    mock_client.get.return_value = response

    with patch(
        "requests_app.infrastructure.gateways.api_delpi_adapter.httpx.Client",
        return_value=mock_client,
    ):
        with pytest.raises(ApplicationError) as exc:
            adapter.search_parties(
                party_type="customer",
                query="weg",
                authorization="Bearer x",
            )
    assert exc.value.status_code == 401
    assert "autenticar" in exc.value.message.lower()
