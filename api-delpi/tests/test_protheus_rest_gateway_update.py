"""Gateway tests — supplier PUT error codes and no retry."""

from __future__ import annotations

from unittest.mock import MagicMock

import httpx
import pytest

from app.domain.integrations.protheus_rest import ProtheusRestConfig, ProtheusRestError
from app.infrastructure.gateways.protheus_rest_gateway import ProtheusRestGateway

_CONFIG = ProtheusRestConfig(
    username="u",
    password="p",
    base_url="https://protheus.example/rest",
    auth_path="/api/oauth2/v1/token",
    suppliers_path="/delpi/api/v1/suppliers",
)


def _response(status: int, payload: dict | None = None) -> httpx.Response:
    return httpx.Response(
        status,
        json=payload or {},
        request=httpx.Request("PUT", "https://protheus.example/rest/suppliers/00000101"),
    )


def test_update_maps_001_to_004() -> None:
    client = MagicMock()
    gw = ProtheusRestGateway(client=client)
    cases = [
        (400, {"code_error": "001"}, "PROTHEUS_SUPPLIER_WRITE_INVALID_ID"),
        (400, {"code_error": "002", "error": "JSON inválido"}, "PROTHEUS_SUPPLIER_WRITE_INVALID_JSON"),
        (400, {"code_error": "003", "error": "Falha ao alterar fornecedor"}, "PROTHEUS_SUPPLIER_UPDATE_MATA020_FAILED"),
        (404, {"code_error": "004"}, "PROTHEUS_SUPPLIER_NOT_FOUND"),
    ]
    for status, payload, code in cases:
        client.request.return_value = _response(status, payload)
        with pytest.raises(ProtheusRestError) as exc:
            gw.update_supplier(
                _CONFIG,
                supplier_id="00000101",
                body={"codusr": "000161", "fornecedor": [{"supplier_name": "X"}]},
                access_token="secret-token",
            )
        assert exc.value.code == code
        assert client.request.call_count == 1
        client.request.reset_mock()


def test_update_timeout_single_attempt() -> None:
    client = MagicMock()
    client.request.side_effect = httpx.TimeoutException("timeout")
    gw = ProtheusRestGateway(client=client)
    with pytest.raises(ProtheusRestError) as exc:
        gw.update_supplier(
            _CONFIG,
            supplier_id="00000101",
            body={"codusr": "000161", "fornecedor": [{"supplier_name": "X"}]},
            access_token="t",
        )
    assert exc.value.code == "PROTHEUS_TIMEOUT"
    assert client.request.call_count == 1


def test_update_2xx_does_not_claim_persistence() -> None:
    client = MagicMock()
    client.request.return_value = _response(200, {"message": "ok"})
    result = ProtheusRestGateway(client=client).update_supplier(
        _CONFIG,
        supplier_id="00000101",
        body={"codusr": "000161", "fornecedor": [{"supplier_name": "X"}]},
        access_token="t",
    )
    assert result["update_acknowledged"] is True
    assert result["persistence_proven"] is False
    assert result["update_confirmed"] is False
