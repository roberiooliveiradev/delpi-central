"""Contract tests — supplier PUT payload (object in, array upstream)."""

from __future__ import annotations

import pytest

from app.application.services.integrations.protheus_supplier_update_payload import (
    build_upstream_update_body,
    normalize_supplier_update_fields,
    validate_supplier_id,
)
from app.domain.integrations.protheus_rest import ProtheusRestError


def test_id_preserves_leading_zeros() -> None:
    assert validate_supplier_id("00000101") == "00000101"


def test_id_invalid() -> None:
    with pytest.raises(ProtheusRestError) as exc:
        validate_supplier_id("101")
    assert exc.value.code == "PROTHEUS_SUPPLIER_ID_INVALID"


def test_upstream_is_array_and_omits_absent_fields() -> None:
    fields = normalize_supplier_update_fields({"supplier_name": "NOME ATUALIZADO"})
    body = build_upstream_update_body(codusr="000161", fields=fields)
    assert body["codusr"] == "000161"
    assert isinstance(body["fornecedor"], list)
    assert body["fornecedor"] == [{"supplier_name": "NOME ATUALIZADO"}]
    assert "supplier_short_name" not in body["fornecedor"][0]


def test_rejects_unknown_and_post_only_fields() -> None:
    with pytest.raises(ProtheusRestError) as exc:
        normalize_supplier_update_fields({"tax_id": "00000000000191"})
    assert exc.value.code == "PROTHEUS_SUPPLIER_FIELD_NOT_EDITABLE"


def test_rejects_empty_and_explicit_clear() -> None:
    with pytest.raises(ProtheusRestError) as exc:
        normalize_supplier_update_fields({})
    assert exc.value.code == "PROTHEUS_SUPPLIER_PAYLOAD_INVALID"
    with pytest.raises(ProtheusRestError) as exc2:
        normalize_supplier_update_fields({"supplier_name": ""})
    assert exc2.value.code == "PROTHEUS_SUPPLIER_CLEAR_NOT_SUPPORTED"
    with pytest.raises(ProtheusRestError) as exc3:
        normalize_supplier_update_fields({"supplier_short_name": None})
    assert exc3.value.code == "PROTHEUS_SUPPLIER_CLEAR_NOT_SUPPORTED"


def test_rejects_identity_mutation() -> None:
    with pytest.raises(ProtheusRestError) as exc:
        normalize_supplier_update_fields({"codusr": "000161", "supplier_name": "X"})
    assert exc.value.code == "PROTHEUS_IDENTITY_CLIENT_FORBIDDEN"


def test_length_not_truncated() -> None:
    with pytest.raises(ProtheusRestError) as exc:
        normalize_supplier_update_fields({"supplier_short_name": "X" * 21})
    assert exc.value.code == "PROTHEUS_SUPPLIER_PAYLOAD_INVALID"
