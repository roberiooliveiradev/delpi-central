"""Payload tests — product PUT full-representation contract and URL derivation."""

from __future__ import annotations

import pytest

from app.application.services.integrations.protheus_product_payload import (
    PRODUCT_FIELD_SPECS,
    build_upstream_product_update_body,
    normalize_product_update_fields,
    product_update_url,
    validate_product_code,
)
from app.domain.integrations.protheus_rest import ProtheusRestConfig, ProtheusRestError

FULL_PRODUCT = {
    "B1_GRUPO": "1045",
    "B1_DESC": "PESO PARA TESTE 6KG",
    "B1_REFEREN": "",
    "B1_REFCANT": "",
    "B1_CODDES": "",
    "B1_TIPO": "MC",
    "B1_YHOHS": "N",
    "B1_POSIPI": "72141010",
    "B1_LOCPAD": "01",
    "B1_UM": "PC",
    "B1_SEGUM": "",
    "B1_TE": "001",
    "B1_TS": "",
    "B1_PICMRET": "0.0",
    "B1_CONV": "0.0",
    "B1_TIPCONV": "M",
    "B1_TPMAT": "1",
    "B1_ESPECIE": "0",
    "B1_EX_NCM": "",
    "B1_EX_NBM": "",
    "B1_ORIGEM": "0",
}


def test_validate_product_code_ok() -> None:
    assert validate_product_code(" ABC123 ") == "ABC123"


def test_validate_product_code_rejects_bad() -> None:
    with pytest.raises(ProtheusRestError) as exc:
        validate_product_code("A B!")
    assert exc.value.code == "PROTHEUS_PRODUCT_ID_INVALID"
    with pytest.raises(ProtheusRestError):
        validate_product_code("")
    with pytest.raises(ProtheusRestError):
        validate_product_code("X" * 16)


def test_normalize_accepts_full_representation() -> None:
    out = normalize_product_update_fields(FULL_PRODUCT)
    assert out["B1_DESC"] == "PESO PARA TESTE 6KG"
    assert out["B1_REFEREN"] == ""
    assert set(out) == set(PRODUCT_FIELD_SPECS)


def test_normalize_rejects_partial_body() -> None:
    partial = {k: v for k, v in FULL_PRODUCT.items() if k != "B1_ESPECIE"}
    with pytest.raises(ProtheusRestError) as exc:
        normalize_product_update_fields(partial)
    assert exc.value.code == "PROTHEUS_PRODUCT_FULL_REPRESENTATION_REQUIRED"
    assert "B1_ESPECIE" in exc.value.message


def test_normalize_rejects_unknown_field() -> None:
    with pytest.raises(ProtheusRestError) as exc:
        normalize_product_update_fields({**FULL_PRODUCT, "B1_XPTO": "1"})
    assert exc.value.code == "PROTHEUS_PRODUCT_FIELD_UNKNOWN"


def test_normalize_rejects_identity_keys() -> None:
    for key in ("B1_COD", "codusr", "protheus_user_id"):
        with pytest.raises(ProtheusRestError) as exc:
            normalize_product_update_fields({**FULL_PRODUCT, key: "X"})
        assert exc.value.code == "PROTHEUS_IDENTITY_CLIENT_FORBIDDEN"


def test_normalize_rejects_null_allows_empty() -> None:
    with pytest.raises(ProtheusRestError) as exc:
        normalize_product_update_fields({**FULL_PRODUCT, "B1_DESC": None})
    assert exc.value.code == "PROTHEUS_PRODUCT_PAYLOAD_INVALID"
    out = normalize_product_update_fields({**FULL_PRODUCT, "B1_REFEREN": ""})
    assert out["B1_REFEREN"] == ""


def test_normalize_rejects_oversized() -> None:
    with pytest.raises(ProtheusRestError) as exc:
        normalize_product_update_fields({**FULL_PRODUCT, "B1_DESC": "X" * 101})
    assert exc.value.code == "PROTHEUS_PRODUCT_FIELD_TOO_LONG"


def test_normalize_rejects_non_numeric_numeric_field() -> None:
    with pytest.raises(ProtheusRestError) as exc:
        normalize_product_update_fields({**FULL_PRODUCT, "B1_PICMRET": "abc"})
    assert exc.value.code == "PROTHEUS_PRODUCT_PAYLOAD_INVALID"


def test_upstream_body_is_flat_b1() -> None:
    body = build_upstream_product_update_body(
        product_code="ABC123", fields=normalize_product_update_fields(FULL_PRODUCT)
    )
    assert body["B1_COD"] == "ABC123"
    assert body["B1_DESC"] == "PESO PARA TESTE 6KG"
    assert "codusr" not in body


def test_product_update_url_prod_shape() -> None:
    config = ProtheusRestConfig(
        username="u",
        password="p",
        base_url="http://192.168.1.231:8061",
        auth_path="/restall/api/oauth2/v1/token",
        suppliers_path="/restall/delpi/api/v1/suppliers",
    )
    assert (
        product_update_url(config)
        == "http://192.168.1.231:8061/restall/delpiproduto/v1/IncProduto/alterar"
    )


def test_product_update_url_tst_shape() -> None:
    config = ProtheusRestConfig(
        username="u",
        password="p",
        base_url="http://192.168.1.233:8701/rest",
        auth_path="/api/oauth2/v1/token",
        suppliers_path="/delpi/api/v1/suppliers",
    )
    assert (
        product_update_url(config)
        == "http://192.168.1.233:8701/rest/delpiproduto/v1/IncProduto/alterar"
    )


def test_product_update_url_fails_closed_without_marker() -> None:
    config = ProtheusRestConfig(
        username="u",
        password="p",
        base_url="http://example.invalid",
        auth_path="/api/oauth2/v1/token",
        suppliers_path="/api/v1/suppliers",
    )
    with pytest.raises(ProtheusRestError) as exc:
        product_update_url(config)
    assert exc.value.code == "PROTHEUS_CONFIG_INVALID"
