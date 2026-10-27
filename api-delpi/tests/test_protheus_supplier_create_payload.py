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

# X4.PROD-C1.R6 — unconditional required set proven by the R5 productive
# failure + E2 homologation (upstream "Campos Obrigatorios Não Preenchidos").
REQUIRED_CREATE = {
    "supplier_store": "01",
    "rohs_indicator": "N",
    "accounting_account": "00000000",
    "bacen_country_code": "01058",
    "payment_method_code": "01",
    "financial_nature_code": "0000",
    "payment_condition_code": "010",
}


def test_normalize_preserves_leading_zeros() -> None:
    out = normalize_supplier_fields(
        {
            **REQUIRED_CREATE,
            "tax_id": "00000000000191",
            "postal_code": "88000000",
            "city_code": "00001",
        }
    )
    assert out["supplier_store"] == "01"
    assert out["tax_id"] == "00000000000191"
    assert out["bacen_country_code"] == "01058"
    assert out["payment_condition_code"] == "010"


def test_rejects_numeric_tax_id_that_would_drop_zeros() -> None:
    with pytest.raises(ProtheusRestError) as exc:
        normalize_supplier_fields({**REQUIRED_CREATE, "tax_id": 191})
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
    assert normalize_supplier_fields(
        {**REQUIRED_CREATE, "person_type": "J"}
    )["person_type"] == "J"
    with pytest.raises(ProtheusRestError):
        normalize_supplier_fields({**REQUIRED_CREATE, "person_type": "Z"})


def test_requires_supplier_store() -> None:
    with pytest.raises(ProtheusRestError) as exc:
        normalize_supplier_fields(
            {k: v for k, v in REQUIRED_CREATE.items() if k != "supplier_store"}
        )
    assert exc.value.code == "SUPPLIER_REQUIRED_FIELDS_MISSING"
    assert [e["field"] for e in exc.value.fields] == ["supplier_store"]


def test_missing_six_r5_fields_aggregates_all() -> None:
    """R6 — a single 422 names every missing required field."""
    with pytest.raises(ProtheusRestError) as exc:
        normalize_supplier_fields({"supplier_store": "01"})
    assert exc.value.code == "SUPPLIER_REQUIRED_FIELDS_MISSING"
    assert exc.value.status_code == 422
    assert {e["field"] for e in exc.value.fields} == {
        "payment_condition_code",
        "bacen_country_code",
        "accounting_account",
        "financial_nature_code",
        "rohs_indicator",
        "payment_method_code",
    }
    assert all(e["code"] == "missing_required" for e in exc.value.fields)


def test_whitespace_only_required_counts_as_missing() -> None:
    with pytest.raises(ProtheusRestError) as exc:
        normalize_supplier_fields(
            {**REQUIRED_CREATE, "accounting_account": "   "}
        )
    assert exc.value.code == "SUPPLIER_REQUIRED_FIELDS_MISSING"
    assert [e["field"] for e in exc.value.fields] == ["accounting_account"]


def test_mixed_missing_and_invalid_aggregates() -> None:
    with pytest.raises(ProtheusRestError) as exc:
        normalize_supplier_fields(
            {
                "supplier_store": "01",
                "person_type": "Z",  # invalid enum
                # six R5 fields absent
            }
        )
    assert exc.value.code == "PROTHEUS_SUPPLIER_PAYLOAD_INVALID"
    assert len(exc.value.fields) == 7
    assert {
        e["field"] for e in exc.value.fields if e["code"] == "invalid_value"
    } == {"person_type"}


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
    payload = {**REQUIRED_CREATE, "person_type": "J", field: raw}
    out = normalize_supplier_fields(payload)
    assert out[field] == expected


@pytest.mark.parametrize("field", UNPROVEN_E3_FIELDS)
def test_unproven_e3_field_still_rejected(field: str) -> None:
    with pytest.raises(ProtheusRestError) as exc:
        normalize_supplier_fields({**REQUIRED_CREATE, field: "1"})
    assert exc.value.code == "PROTHEUS_SUPPLIER_PAYLOAD_INVALID"


def test_promoted_field_invalid_values_rejected() -> None:
    with pytest.raises(ProtheusRestError):
        normalize_supplier_fields({**REQUIRED_CREATE, "irf_calculation": "9"})
    with pytest.raises(ProtheusRestError):
        normalize_supplier_fields({**REQUIRED_CREATE, "po_box": "123456"})
    with pytest.raises(ProtheusRestError):
        normalize_supplier_fields({**REQUIRED_CREATE, "fax": "FAX"})


def test_cnae_conditional_rule_published() -> None:
    with pytest.raises(ProtheusRestError) as exc:
        normalize_supplier_fields(
            {**REQUIRED_CREATE, "person_type": "F", "cnae_code": "4711301"}
        )
    assert exc.value.code == "PROTHEUS_SUPPLIER_FIELD_CONDITIONAL"
    assert [e["field"] for e in exc.value.fields] == ["cnae_code"]
    for person in ("J", "X"):
        out = normalize_supplier_fields(
            {**REQUIRED_CREATE, "person_type": person, "cnae_code": "4711301"}
        )
        assert out["cnae_code"] == "4711301"


def test_published_allowlist_size() -> None:
    # 24 original + 29 E2-proven promoted in E3
    assert len(SUPPLIER_FIELD_SPECS) == 53
