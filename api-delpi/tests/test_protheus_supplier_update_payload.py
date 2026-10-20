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


def test_rejects_tax_id_and_identity_fields_as_immutable() -> None:
    for key in ("tax_id", "supplier_code", "supplier_store", "a2_filial"):
        with pytest.raises(ProtheusRestError) as exc:
            normalize_supplier_update_fields({key: "01"})
        assert exc.value.code == "PROTHEUS_SUPPLIER_FIELD_IMMUTABLE"


def test_rejects_unknown_fields() -> None:
    with pytest.raises(ProtheusRestError) as exc:
        normalize_supplier_update_fields({"not_a_field": "x"})
    assert exc.value.code == "PROTHEUS_SUPPLIER_FIELD_NOT_EDITABLE"


def test_accepts_extended_cadastral_fields() -> None:
    fields = normalize_supplier_update_fields(
        {
            "address": "RUA NOVA",
            "district": "CENTRO",
            "postal_code": "89120000",
            "state": "sc",
            "city": "TIMBO",
            "city_code": "18202",
            "area_code": "047",
            "phone": "99999",
            "contact_name": "MARIA",
            "email": "a@b.com",
            "state_registration": "123456",
            "municipal_registration": "789",
            "country_code": "105",
            "bacen_country_code": "01058",
            "rohs_indicator": "N",
            "payment_condition_code": "010",
            "payment_method_code": "01",
            "accounting_account": "00000001",
            "financial_nature_code": "0001",
            "person_type": "J",
        }
    )
    assert len(fields) == 20
    assert fields["state"] == "SC"  # upper applied
    assert fields["rohs_indicator"] == "N"  # enum S/N enforced
    assert fields["postal_code"] == "89120000"  # leading zeros preserved


def test_multi_field_partial_put_preserves_omitted() -> None:
    fields = normalize_supplier_update_fields({"city": "TIMBO", "phone": "1"})
    assert fields == {"city": "TIMBO", "phone": "1"}


def test_extended_fields_validation() -> None:
    with pytest.raises(ProtheusRestError) as exc:
        normalize_supplier_update_fields({"postal_code": "12A4"})
    assert exc.value.code == "PROTHEUS_SUPPLIER_PAYLOAD_INVALID"
    with pytest.raises(ProtheusRestError) as exc2:
        normalize_supplier_update_fields({"person_type": "Z"})
    assert exc2.value.code == "PROTHEUS_SUPPLIER_PAYLOAD_INVALID"
    with pytest.raises(ProtheusRestError) as exc3:
        normalize_supplier_update_fields({"email": "sem-arroba"})
    assert exc3.value.code == "PROTHEUS_SUPPLIER_PAYLOAD_INVALID"
    with pytest.raises(ProtheusRestError) as exc4:
        normalize_supplier_update_fields({"city": "x" * 26})
    assert exc4.value.code == "PROTHEUS_SUPPLIER_PAYLOAD_INVALID"


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
