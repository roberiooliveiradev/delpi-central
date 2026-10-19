"""Contract tests — supplier POST payload normalization."""

from __future__ import annotations

import pytest

from app.application.services.integrations.protheus_supplier_create_payload import (
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
