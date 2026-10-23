"""Contract tests — supplier POST payload normalization."""

from __future__ import annotations

import pytest

from app.application.services.integrations.protheus_supplier_create_payload import (
    SUPPLIER_FIELD_SPECS,
    build_upstream_create_body,
    normalize_supplier_fields,
    validate_codusr,
)
from app.domain.integrations.protheus_rest import ProtheusRestError


def test_normalize_preserves_leading_zeros() -> None:
    out = normalize_supplier_fields(
        {
            "supplier_store": "01",
            "tax_id": "00000000000191",
            "postal_code": "88000000",
            "city_code": "00001",
            "bacen_country_code": "01058",
            "accounting_account": "00000000",
            "financial_nature_code": "0000",
            "payment_method_code": "01",
            "payment_condition_code": "010",
        }
    )
    assert out["supplier_store"] == "01"
    assert out["tax_id"] == "00000000000191"
    assert out["bacen_country_code"] == "01058"
    assert out["payment_condition_code"] == "010"


def test_rejects_numeric_tax_id_that_would_drop_zeros() -> None:
    with pytest.raises(ProtheusRestError) as exc:
        normalize_supplier_fields({"supplier_store": "01", "tax_id": 191})
    assert exc.value.code == "PROTHEUS_SUPPLIER_PAYLOAD_INVALID"


def test_rejects_client_codusr_inside_fornecedor() -> None:
    with pytest.raises(ProtheusRestError) as exc:
        normalize_supplier_fields({"supplier_store": "01", "codusr": "000161"})
    assert exc.value.code == "PROTHEUS_IDENTITY_CLIENT_FORBIDDEN"


def test_rejects_unknown_field() -> None:
    with pytest.raises(ProtheusRestError) as exc:
        normalize_supplier_fields({"supplier_store": "01", "A2_COD": "000001"})
    assert exc.value.code == "PROTHEUS_SUPPLIER_PAYLOAD_INVALID"


def test_person_type_enum() -> None:
    assert normalize_supplier_fields({"supplier_store": "01", "person_type": "J"})[
        "person_type"
    ] == "J"
    with pytest.raises(ProtheusRestError):
        normalize_supplier_fields({"supplier_store": "01", "person_type": "Z"})


def test_requires_supplier_store() -> None:
    with pytest.raises(ProtheusRestError) as exc:
        normalize_supplier_fields({"supplier_name": "ACME"})
    assert exc.value.code == "PROTHEUS_SUPPLIER_PAYLOAD_INVALID"


def test_build_upstream_body_object_not_array() -> None:
    body = build_upstream_create_body(
        codusr="000161",
        fornecedor={"supplier_store": "01", "supplier_name": "ACME"},
    )
    assert body["codusr"] == "000161"
    assert isinstance(body["fornecedor"], dict)
    assert body["fornecedor"]["supplier_store"] == "01"


def test_validate_codusr_six_digits() -> None:
    assert validate_codusr("000161") == "000161"
    with pytest.raises(ProtheusRestError) as exc:
        validate_codusr("161")
    assert exc.value.code == "PROTHEUS_IDENTITY_INVALID"


# --- X4.FIELDS.E3 — promoted (E2 persistence-proven) fields --------------

PROMOTED_E3_FIELDS = {
    "address_number": ("38500", "38500"),
    "po_box": ("1234", "1234"),
    "icms_contributor": ("1", "1"),
    "simples_nacional": ("2", "2"),
    "cnae_code": ("6201501", "6201501"),
    "legal_entity_type": ("1", "1"),
    "simp_regime_code": ("1", "1"),
    "pb_regime_code": ("1", "1"),
    "inss_withholding": ("N", "N"),
    "iss_withholding": ("N", "N"),
    "csll_withholding": ("2", "2"),
    "cofins_withholding": ("2", "2"),
    "pis_withholding": ("2", "2"),
    "irf_calculation": ("2", "2"),
    "inp_calculation": ("2", "2"),
    "tax_group_code": ("001", "001"),
    "commercial_contact_name": ("ZZ COM", "ZZ COM"),
    "fax": ("4730000000", "4730000000"),
    "website": ("www.exemplo.test", "www.exemplo.test"),
    "responsible_name": ("ZZ RESP", "ZZ RESP"),
    "risk_code": ("001", "001"),
    "swift_code": ("banxbrscxxx", "BANXBRSCXXX"),
    "carrier_code": ("000001", "000001"),
    "segment_code": ("000001", "000001"),
    "administrator_code": ("001", "001"),
    "linked_customer_code": ("000123", "000123"),
    "linked_customer_store": ("01", "01"),
    "linked_employee_code": ("000007", "000007"),
    "purchase_price_table_code": ("001", "001"),
}

UNPROVEN_E3_FIELDS = (
    "person_category",
    "payee_code",
    "payee_store",
    "generic_supplier",
    "country_calling_code",
    "link_type_code",
    "esocial_category_code",
)


@pytest.mark.parametrize("field", sorted(PROMOTED_E3_FIELDS))
def test_promoted_e3_field_accepted(field: str) -> None:
    raw, expected = PROMOTED_E3_FIELDS[field]
    out = normalize_supplier_fields({"supplier_store": "01", field: raw})
    assert out[field] == expected


@pytest.mark.parametrize("field", UNPROVEN_E3_FIELDS)
def test_unproven_e3_field_still_rejected(field: str) -> None:
    with pytest.raises(ProtheusRestError) as exc:
        normalize_supplier_fields({"supplier_store": "01", field: "1"})
    assert exc.value.code == "PROTHEUS_SUPPLIER_PAYLOAD_INVALID"


def test_promoted_field_invalid_values_rejected() -> None:
    with pytest.raises(ProtheusRestError):
        normalize_supplier_fields({"supplier_store": "01", "irf_calculation": "9"})
    with pytest.raises(ProtheusRestError):
        normalize_supplier_fields({"supplier_store": "01", "po_box": "123456"})
    with pytest.raises(ProtheusRestError):
        normalize_supplier_fields({"supplier_store": "01", "fax": "FAX"})


def test_cnae_conditional_rule_published() -> None:
    with pytest.raises(ProtheusRestError) as exc:
        normalize_supplier_fields(
            {"supplier_store": "01", "person_type": "F", "cnae_code": "4711301"}
        )
    assert exc.value.code == "PROTHEUS_SUPPLIER_FIELD_CONDITIONAL"
    for person in ("J", "X"):
        out = normalize_supplier_fields(
            {"supplier_store": "01", "person_type": person, "cnae_code": "4711301"}
        )
        assert out["cnae_code"] == "4711301"


def test_published_allowlist_size() -> None:
    # 24 original + 29 E2-proven promoted in E3
    assert len(SUPPLIER_FIELD_SPECS) == 53
