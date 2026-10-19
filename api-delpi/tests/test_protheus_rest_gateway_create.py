"""Gateway tests — supplier POST error mapping and no write retry."""

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
        request=httpx.Request("POST", "https://protheus.example/rest/delpi/api/v1/suppliers"),
    )


def test_create_maps_code_001_json_vs_id() -> None:
    client = MagicMock()
    client.request.side_effect = [
        _response(400, {"code_error": "001", "error": "JSON inválido"}),
    ]
    gw = ProtheusRestGateway(client=client)
    with pytest.raises(ProtheusRestError) as exc:
        gw.create_supplier(
            _CONFIG, body={"codusr": "000161", "fornecedor": {}}, access_token="t"
        )
    assert exc.value.code == "PROTHEUS_SUPPLIER_WRITE_INVALID_JSON"

    client.request.side_effect = [
        _response(400, {"code_error": "001", "error": "ID inválido"}),
    ]
    with pytest.raises(ProtheusRestError) as exc2:
        gw.create_supplier(
            _CONFIG, body={"codusr": "000161", "fornecedor": {}}, access_token="t"
        )
    assert exc2.value.code == "PROTHEUS_SUPPLIER_WRITE_INVALID_ID"


def test_create_maps_002_and_003() -> None:
    client = MagicMock()
    client.request.return_value = _response(
        400, {"code_error": "002", "error": "campo obrigatório"}
    )
    gw = ProtheusRestGateway(client=client)
    with pytest.raises(ProtheusRestError) as exc:
        gw.create_supplier(
            _CONFIG, body={"codusr": "000161", "fornecedor": {}}, access_token="t"
        )
    assert exc.value.code == "PROTHEUS_SUPPLIER_WRITE_REQUIRED_FIELDS"

    client.request.return_value = _response(
        400, {"code_error": "003", "error": "Falha ao alterar fornecedor"}
    )
    with pytest.raises(ProtheusRestError) as exc2:
        gw.create_supplier(
            _CONFIG, body={"codusr": "000161", "fornecedor": {}}, access_token="t"
        )
    assert exc2.value.code == "PROTHEUS_SUPPLIER_WRITE_MATA020_FAILED"


def test_create_timeout_no_retry() -> None:
    client = MagicMock()
    client.request.side_effect = httpx.TimeoutException("timeout")
    gw = ProtheusRestGateway(client=client)
    with pytest.raises(ProtheusRestError) as exc:
        gw.create_supplier(
            _CONFIG, body={"codusr": "000161", "fornecedor": {}}, access_token="t"
        )
    assert exc.value.code == "PROTHEUS_TIMEOUT"
    assert client.request.call_count == 1


def test_create_5xx() -> None:
    client = MagicMock()
    client.request.return_value = _response(503, {"message": "down"})
    gw = ProtheusRestGateway(client=client)
    with pytest.raises(ProtheusRestError) as exc:
        gw.create_supplier(
            _CONFIG, body={"codusr": "000161", "fornecedor": {}}, access_token="t"
        )
    assert exc.value.code == "PROTHEUS_UPSTREAM_ERROR"
    assert client.request.call_count == 1


def test_create_success_without_inventing_code() -> None:
    client = MagicMock()
    client.request.return_value = _response(200, {"message": "ok"})
    gw = ProtheusRestGateway(client=client)
    result = gw.create_supplier(
        _CONFIG,
        body={"codusr": "000161", "fornecedor": {"supplier_store": "01"}},
        access_token="t",
    )
    assert result["creation_confirmed"] is False
    assert result["supplier_code"] is None
    assert result["write_outcome"] == "accepted_by_upstream"


def test_create_does_not_log_token(caplog) -> None:
    import logging

    client = MagicMock()
    client.request.return_value = _response(200, {"message": "ok"})
    gw = ProtheusRestGateway(client=client)
    with caplog.at_level(logging.INFO):
        gw.create_supplier(
            _CONFIG,
            body={"codusr": "000161", "fornecedor": {"supplier_store": "01"}},
            access_token="super-secret-token-value",
        )
    joined = " ".join(r.message for r in caplog.records).lower()
    assert "super-secret-token-value" not in joined
