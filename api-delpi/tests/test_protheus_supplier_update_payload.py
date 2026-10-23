"""Contract tests — supplier PUT payload (object in, array upstream)."""

from __future__ import annotations

import pytest

from app.application.services.integrations.protheus_supplier_update_payload import (
    PUT_EDITABLE_FIELDS,
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


def test_upstream_is_object_and_omits_absent_fields() -> None:
    # F4 live evidence: upstream PUT accepts `fornecedor` as OBJECT;
    # the documented array form returns HTTP 500 upstream.
    fields = normalize_supplier_update_fields({"supplier_name": "NOME ATUALIZADO"})
    body = build_upstream_update_body(codusr="000161", fields=fields)
    assert body["codusr"] == "000161"
    assert isinstance(body["fornecedor"], dict)
    assert body["fornecedor"] == {"supplier_name": "NOME ATUALIZADO"}
    assert "supplier_short_name" not in body["fornecedor"]


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


# --- X4.FIELDS.E5 — PUT homologated set (26) vs still-unproven (3) ------

E5_PUT_HOMOLOGATED_FIELDS = (
    "address_number",
    "po_box",
    "icms_contributor",
    "simples_nacional",
    "cnae_code",
    "legal_entity_type",
    "pb_regime_code",
    "inss_withholding",
    "iss_withholding",
    "csll_withholding",
    "cofins_withholding",
    "pis_withholding",
    "irf_calculation",
    "inp_calculation",
    "tax_group_code",
    "commercial_contact_name",
    "fax",
    "website",
    "responsible_name",
    "risk_code",
    "swift_code",
    "purchase_price_table_code",
    "carrier_code",
    "segment_code",
    "administrator_code",
    "linked_employee_code",
)

# E5 assay outcomes that stay OUT of the PUT allowlist:
# - simp_regime_code: upstream accepts 1/2 but no controlled change could be
#   proven (field drifts between reads); "0" is rejected upstream.
# - linked_customer_code: SA1 TST01 only has customer 000001 — no distinct
#   value exists to prove an update; the composite pair PUT was rejected.
# - linked_customer_store: PUT sent a valid SA1 store and A2_LOJCLI stayed
#   unchanged — upstream ignores it on update.
E5_NOT_HOMOLOGATED_FIELDS = (
    "simp_regime_code",
    "linked_customer_code",
    "linked_customer_store",
)


_E5_SAMPLE_VALUES = {
    "inss_withholding": "S",
    "iss_withholding": "S",
}


@pytest.mark.parametrize("field", E5_PUT_HOMOLOGATED_FIELDS)
def test_e5_put_homologated_field_accepted(field: str) -> None:
    value = _E5_SAMPLE_VALUES.get(field, "1")
    fields = normalize_supplier_update_fields({field: value})
    assert fields == {field: value}


@pytest.mark.parametrize("field", E5_NOT_HOMOLOGATED_FIELDS)
def test_e5_not_homologated_field_rejected_in_put(field: str) -> None:
    with pytest.raises(ProtheusRestError) as exc:
        normalize_supplier_update_fields({field: "1"})
    assert exc.value.code == "PROTHEUS_SUPPLIER_FIELD_NOT_EDITABLE"


def test_e5_put_normalization_preserves_spec_rules() -> None:
    fields = normalize_supplier_update_fields({"swift_code": "b1"})
    assert fields["swift_code"] == "B1"
    with pytest.raises(ProtheusRestError) as exc:
        normalize_supplier_update_fields({"icms_contributor": "9"})
    assert exc.value.code == "PROTHEUS_SUPPLIER_PAYLOAD_INVALID"
    with pytest.raises(ProtheusRestError) as exc:
        normalize_supplier_update_fields({"address_number": "12x"})
    assert exc.value.code == "PROTHEUS_SUPPLIER_PAYLOAD_INVALID"


def test_e5_cnae_conditional_enforced_when_person_type_f() -> None:
    with pytest.raises(ProtheusRestError) as exc:
        normalize_supplier_update_fields(
            {"cnae_code": "6202300", "person_type": "F"}
        )
    assert exc.value.code == "PROTHEUS_SUPPLIER_FIELD_CONDITIONAL"


def test_put_allowlist_is_f3_3_plus_e5_proven() -> None:
    assert len(PUT_EDITABLE_FIELDS) == 22 + 26
    for field in E5_NOT_HOMOLOGATED_FIELDS:
        assert field not in PUT_EDITABLE_FIELDS
    assert "tax_id" not in PUT_EDITABLE_FIELDS
    assert "supplier_store" not in PUT_EDITABLE_FIELDS
