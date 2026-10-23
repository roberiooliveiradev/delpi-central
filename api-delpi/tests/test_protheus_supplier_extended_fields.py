"""X4.FIELDS.E1–E3 — local experiment tests for extended supplier fields.

Scope: serialization/validation only, against the isolated experimental
module. NO upstream call is made. After X4.FIELDS.E3 the 29 proven fields
live in the published contract — this module retains only the 7 candidates
without persistence evidence, and the published allowlist must keep
rejecting exactly those (tests assert both directions).
"""

from __future__ import annotations

import pytest

from app.application.services.integrations.protheus_supplier_create_payload import (
    SUPPLIER_FIELD_SPECS,
    normalize_supplier_fields,
)
from app.application.services.integrations.protheus_supplier_extended_fields import (
    EXPERIMENTAL_BLOCKED_FIELDS,
    EXPERIMENTAL_POST_ALLOWLIST,
    EXPERIMENTAL_PUT_ALLOWLIST,
    SUPPLIER_EXTENDED_FIELD_SPECS,
    build_upstream_create_body_experimental,
    normalize_experimental_supplier_fields,
)
from app.domain.integrations.protheus_rest import ProtheusRestError

BASE_PAYLOAD = {
    "supplier_store": "01",
    "person_type": "J",
    "tax_id": "00000000000191",
    "supplier_name": "FORNECEDOR EXPERIMENTO",
    "state": "SC",
    "phone": "99999999",
    "financial_nature_code": "0001",
    "bacen_country_code": "01058",
}

# field -> (input, expected_normalized) — only the 7 unproven candidates
# still held by the experimental module (E3 promoted the other 29).
CANDIDATE_CASES = {
    "person_category": ("PJ", "PJ"),
    "esocial_category_code": ("701", "701"),
    "country_calling_code": ("55", "55"),
    "payee_code": ("000905", "000905"),
    "payee_store": ("04", "04"),
    "generic_supplier": ("S", "S"),
    "link_type_code": ("01", "01"),
}

# field -> invalid value
INVALID_CASES = {
    "payee_store": "004",  # length 3 > 2
}


def test_public_allowlist_unchanged_by_experiment() -> None:
    """Published contract must still reject every candidate field."""
    for field in SUPPLIER_EXTENDED_FIELD_SPECS:
        with pytest.raises(ProtheusRestError) as exc:
            normalize_supplier_fields({**BASE_PAYLOAD, field: "1"})
        assert exc.value.code == "PROTHEUS_SUPPLIER_PAYLOAD_INVALID"


def test_experiment_preserves_current_payload_compatibility() -> None:
    experimental = normalize_experimental_supplier_fields(BASE_PAYLOAD)
    published = normalize_supplier_fields(BASE_PAYLOAD)
    assert experimental == published
    assert set(experimental) == set(published)


@pytest.mark.parametrize("field", sorted(CANDIDATE_CASES))
def test_candidate_field_serializes(field: str) -> None:
    raw_value, expected = CANDIDATE_CASES[field]
    out = normalize_experimental_supplier_fields(
        {**BASE_PAYLOAD, field: raw_value}
    )
    assert out[field] == expected


@pytest.mark.parametrize("field", sorted(INVALID_CASES))
def test_candidate_field_rejects_invalid(field: str) -> None:
    with pytest.raises(ProtheusRestError) as exc:
        normalize_experimental_supplier_fields(
            {**BASE_PAYLOAD, field: INVALID_CASES[field]}
        )
    assert exc.value.code in {
        "PROTHEUS_SUPPLIER_PAYLOAD_INVALID",
        "PROTHEUS_SUPPLIER_FIELD_CONDITIONAL",
    }


def test_numeric_types_rejected_to_preserve_leading_zeros() -> None:
    with pytest.raises(ProtheusRestError) as exc:
        normalize_experimental_supplier_fields(
            {**BASE_PAYLOAD, "po_box": 123, "payee_code": 905}
        )
    assert exc.value.code == "PROTHEUS_SUPPLIER_PAYLOAD_INVALID"


def test_cnae_conditional_requires_juridical_or_exterior() -> None:
    with pytest.raises(ProtheusRestError) as exc:
        normalize_experimental_supplier_fields(
            {**BASE_PAYLOAD, "person_type": "F", "cnae_code": "4711301"}
        )
    assert exc.value.code == "PROTHEUS_SUPPLIER_FIELD_CONDITIONAL"
    for person in ("J", "X"):
        out = normalize_experimental_supplier_fields(
            {**BASE_PAYLOAD, "person_type": person, "cnae_code": "4711301"}
        )
        assert out["cnae_code"] == "4711301"


def test_optional_candidates_omitted_stay_omitted() -> None:
    out = normalize_experimental_supplier_fields(BASE_PAYLOAD)
    for field in SUPPLIER_EXTENDED_FIELD_SPECS:
        assert field not in out


def test_unknown_and_blocked_fields_never_cross_the_allowlist() -> None:
    for field in (*EXPERIMENTAL_BLOCKED_FIELDS, "a2_cgc", "invented_field"):
        with pytest.raises(ProtheusRestError) as exc:
            normalize_experimental_supplier_fields({**BASE_PAYLOAD, field: "1"})
        assert exc.value.code == "PROTHEUS_SUPPLIER_PAYLOAD_INVALID"


def test_client_identity_fields_rejected() -> None:
    for key in ("codusr", "usr_id", "protheus_user_id"):
        with pytest.raises(ProtheusRestError) as exc:
            normalize_experimental_supplier_fields({**BASE_PAYLOAD, key: "000161"})
        assert exc.value.code == "PROTHEUS_IDENTITY_CLIENT_FORBIDDEN"


def test_upstream_body_shape_and_contents() -> None:
    extended = {field: value for field, (value, _exp) in CANDIDATE_CASES.items()}
    out = normalize_experimental_supplier_fields({**BASE_PAYLOAD, **extended})
    body = build_upstream_create_body_experimental(codusr="000161", fornecedor=out)
    assert body["codusr"] == "000161"
    assert isinstance(body["fornecedor"], dict)
    assert "codusr" not in body["fornecedor"]
    assert set(body["fornecedor"]) == set(out)
    # every sent key is allowlisted
    assert set(body["fornecedor"]) <= EXPERIMENTAL_POST_ALLOWLIST


def test_experimental_put_allowlist_excludes_document_and_store() -> None:
    assert "tax_id" not in EXPERIMENTAL_PUT_ALLOWLIST
    assert "supplier_store" not in EXPERIMENTAL_PUT_ALLOWLIST
    assert "supplier_code" not in EXPERIMENTAL_PUT_ALLOWLIST
    # all extended candidates are editable candidates in the experiment
    assert set(SUPPLIER_EXTENDED_FIELD_SPECS) <= EXPERIMENTAL_PUT_ALLOWLIST


def test_spec_table_disjoint_from_published_and_complete() -> None:
    assert not (set(SUPPLIER_EXTENDED_FIELD_SPECS) & set(SUPPLIER_FIELD_SPECS))
    assert len(CANDIDATE_CASES) == len(SUPPLIER_EXTENDED_FIELD_SPECS)
    assert set(CANDIDATE_CASES) == set(SUPPLIER_EXTENDED_FIELD_SPECS)
