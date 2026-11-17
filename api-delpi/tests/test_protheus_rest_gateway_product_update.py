"""Gateway tests — product PUT via delpiproduto: 4xx is deterministic REJECTED."""

from __future__ import annotations

from unittest.mock import MagicMock

import httpx
import pytest

from app.domain.integrations.protheus_rest import ProtheusRestError
from app.infrastructure.gateways.protheus_rest_gateway import ProtheusRestGateway

_URL = "https://protheus.example/rest/delpiproduto/v1/IncProduto/alterar"


def _response(
    status: int,
    payload: dict | None = None,
    *,
    content: bytes | None = None,
) -> httpx.Response:
    request = httpx.Request("PUT", _URL)
    if content is not None:
        return httpx.Response(status, content=content, request=request)
    return httpx.Response(status, json=payload or {}, request=request)


def test_product_update_400_with_detail_is_rejected() -> None:
    client = MagicMock()
    client.request.return_value = _response(
        400,
        {
            "code": "400",
            "message": "Erro Log",
            "detailedMessage": "argument #0 error, expected C->U, function val",
        },
    )
    gw = ProtheusRestGateway(client=client)
    with pytest.raises(ProtheusRestError) as exc:
        gw.update_product(url=_URL, body={"B1_COD": "10450043"}, access_token="t")
    assert exc.value.code == "PROTHEUS_PRODUCT_UPDATE_REJECTED"
    assert exc.value.status_code == 400
    assert client.request.call_count == 1


def test_product_update_4xx_bare_body_is_rejected_not_indeterminate() -> None:
    client = MagicMock()
    client.request.return_value = _response(400, {})
    gw = ProtheusRestGateway(client=client)
    with pytest.raises(ProtheusRestError) as exc:
        gw.update_product(url=_URL, body={"B1_COD": "10450043"}, access_token="t")
    assert exc.value.code == "PROTHEUS_PRODUCT_UPDATE_REJECTED"
    assert exc.value.status_code == 400


def test_product_update_4xx_non_utf8_body_is_rejected() -> None:
    client = MagicMock()
    client.request.return_value = _response(
        400,
        content=b'{"code":"400","detailedMessage":"erro \xe7\xe3o inv\xe1lida"}',
    )
    gw = ProtheusRestGateway(client=client)
    with pytest.raises(ProtheusRestError) as exc:
        gw.update_product(url=_URL, body={"B1_COD": "10450043"}, access_token="t")
    assert exc.value.code == "PROTHEUS_PRODUCT_UPDATE_REJECTED"
    assert exc.value.status_code == 400


def test_product_update_5xx_is_upstream_error() -> None:
    client = MagicMock()
    client.request.return_value = _response(503, {})
    gw = ProtheusRestGateway(client=client)
    with pytest.raises(ProtheusRestError) as exc:
        gw.update_product(url=_URL, body={"B1_COD": "10450043"}, access_token="t")
    assert exc.value.code == "PROTHEUS_UPSTREAM_ERROR"
    assert exc.value.status_code == 502


def test_product_update_401_maps_to_token_invalid() -> None:
    client = MagicMock()
    client.request.return_value = _response(401, {})
    gw = ProtheusRestGateway(client=client)
    with pytest.raises(ProtheusRestError) as exc:
        gw.update_product(url=_URL, body={"B1_COD": "10450043"}, access_token="t")
    assert exc.value.code == "PROTHEUS_TOKEN_INVALID"


def test_product_update_timeout_single_attempt() -> None:
    client = MagicMock()
    client.request.side_effect = httpx.TimeoutException("timeout")
    gw = ProtheusRestGateway(client=client)
    with pytest.raises(ProtheusRestError) as exc:
        gw.update_product(url=_URL, body={"B1_COD": "10450043"}, access_token="t")
    assert exc.value.code == "PROTHEUS_TIMEOUT"
    assert client.request.call_count == 1


def test_product_update_2xx_does_not_claim_persistence() -> None:
    client = MagicMock()
    client.request.return_value = _response(
        200,
        {
            "code": "200",
            "message": "OK",
            "detailedMessage": "Registro integrado com sucesso!",
        },
    )
    result = ProtheusRestGateway(client=client).update_product(
        url=_URL, body={"B1_COD": "10450043"}, access_token="t"
    )
    assert result["update_acknowledged"] is True
    assert result["update_confirmed"] is False
    assert result["persistence_proven"] is False
    assert result["http_status"] == 200
