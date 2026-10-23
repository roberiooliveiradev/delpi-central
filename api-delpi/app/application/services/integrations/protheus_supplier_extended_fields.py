"""X4.FIELDS.E1 — experimental supplier extended-field specs (NOT WIRED).

Isolated prototype for candidate cadastral fields of the SA2
PUBLIC_DICTIONARY that are not part of the published POST/PUT contract.
Nothing in the request path imports this module — promotion requires
contract evolution, owner approval and homologation evidence.

Candidate classification follows the de-para (cadastro-fornecedor.md):
- included here: business cadastral fields with clear SX3 type/length;
- excluded and documented in the experiment doc: SYSTEM_GENERATED,
  DO_NOT_SEND, sensitive bank fields (LGPD classification pending),
  NEEDS_REVIEW physical conflicts (A2_ENDCOMP/A2_TIPCTA) and fields
  whose authority belongs to another context (A2_GRUPO → SAD).
"""

from __future__ import annotations

from typing import Any, Mapping

from app.application.services.integrations.protheus_supplier_create_payload import (
    SUPPLIER_FIELD_SPECS,
    normalize_supplier_field_value,
    validate_codusr,
)
from app.domain.integrations.protheus_rest import ProtheusRestError

# Candidate specs — max lengths and validations from SA2 SX3 (§44.3) and
# the PUBLIC_DICTIONARY. ``conditional`` marks fields whose acceptance
# depends on another field's value (WHEN rules), enforced below.
SUPPLIER_EXTENDED_FIELD_SPECS: dict[str, dict[str, Any]] = {
    # --- endereço ---------------------------------------------------------
    "address_number": {"max": 6, "digits": True},
    "po_box": {"max": 5},
    # --- fiscal / tributário ----------------------------------------------
    "icms_contributor": {"max": 1, "enum": frozenset({"", "1", "2"})},
    "simples_nacional": {"max": 1, "enum": frozenset({"", "1", "2"})},
    "cnae_code": {"max": 9, "digits": True, "conditional": "person_type_jx"},
    "legal_entity_type": {"max": 1, "enum": frozenset({"", "1", "2", "3", "4", "5"})},
    "person_category": {"max": 2},
    "simp_regime_code": {"max": 1},
    "pb_regime_code": {"max": 1, "enum": frozenset({"", "1", "2"})},
    "inss_withholding": {"max": 1, "enum": frozenset({"", "S", "N"})},
    "iss_withholding": {"max": 1, "enum": frozenset({"", "S", "N"})},
    "csll_withholding": {"max": 1, "enum": frozenset({"", "1", "2"})},
    "cofins_withholding": {"max": 1, "enum": frozenset({"", "1", "2"})},
    "pis_withholding": {"max": 1, "enum": frozenset({"", "1", "2"})},
    "irf_calculation": {"max": 1, "enum": frozenset({"", "1", "2", "3", "4"})},
    "inp_calculation": {"max": 1, "enum": frozenset({"", "1", "2"})},
    "tax_group_code": {"max": 3},
    "esocial_category_code": {"max": 3},
    # --- contato ----------------------------------------------------------
    "commercial_contact_name": {"max": 15},
    "country_calling_code": {"max": 6},
    "fax": {"max": 15, "digits": True},
    "website": {"max": 30},
    "responsible_name": {"max": 45},
    # --- comercial / referências ------------------------------------------
    "risk_code": {"max": 3},
    "swift_code": {"max": 30, "upper": True},
    "payee_code": {"max": 6, "digits": True},
    "payee_store": {"max": 2, "digits": True},
    "generic_supplier": {"max": 1},
    "purchase_price_table_code": {"max": 3},
    "carrier_code": {"max": 6},
    "segment_code": {"max": 6},
    "link_type_code": {"max": 2},
    "administrator_code": {"max": 3},
    "linked_customer_code": {"max": 6},
    "linked_customer_store": {"max": 2},
    "linked_employee_code": {"max": 6},
}

# Merged experimental table — published contract remains untouched.
EXPERIMENTAL_SUPPLIER_FIELD_SPECS: dict[str, dict[str, Any]] = {
    **SUPPLIER_FIELD_SPECS,
    **SUPPLIER_EXTENDED_FIELD_SPECS,
}

EXPERIMENTAL_POST_ALLOWLIST = frozenset(EXPERIMENTAL_SUPPLIER_FIELD_SPECS)

# Extended PUT allowlist mirrors POST minus document/identity — same rule
# as the published PUT (F3.3). Kept as an explicit constant for the matrix.
EXPERIMENTAL_PUT_ALLOWLIST = frozenset(
    f for f in EXPERIMENTAL_SUPPLIER_FIELD_SPECS if f not in {"tax_id", "supplier_store"}
)

# Fields intentionally NOT candidates — documented, never sent.
EXPERIMENTAL_BLOCKED_FIELDS: dict[str, str] = {
    "address_complement": "NEEDS_REVIEW — conflito físico A2_ENDCOMP×A2_COMPLEM (owner)",
    "bank_code": "SENSITIVE — dados bancários exigem classificação/minimização",
    "bank_branch": "SENSITIVE — dados bancários exigem classificação/minimização",
    "bank_branch_digit": "SENSITIVE — dados bancários exigem classificação/minimização",
    "bank_account": "SENSITIVE — dados bancários exigem classificação/minimização",
    "bank_account_digit": "SENSITIVE — dados bancários exigem classificação/minimização",
    "bank_account_type": "SENSITIVE + NEEDS_REVIEW — A2_TIPCTA×A2_TPCONTA",
    "credit_limit_amount": "DO_NOT_SEND — acumulador estatístico (A2_LC)",
    "branch": "SYSTEM_GENERATED — A2_FILIAL (contexto ERP)",
    "supplier_code": "SYSTEM_GENERATED — A2_COD (GETSXENUM)",
    "blocked": "SYSTEM_GENERATED/RESTRICTED — A2_MSBLQL",
    "group_code": "OUT_OF_CONTEXT — A2_GRUPO não povoado; grupos reais em SAD",
}

_FORBIDDEN_IDENTITY = frozenset(
    {"codusr", "user_id", "usr_id", "protheus_user_id"}
)


def normalize_experimental_supplier_fields(
    raw: Mapping[str, Any] | None,
) -> dict[str, str]:
    """Experimental normalization over the widened allowlist.

    Mirrors ``normalize_supplier_fields`` semantics (unknown → 422,
    identity → 422, absent optional → omitted) plus conditional-field
    rules that the published normalizer does not need yet.
    """
    if raw is None:
        raise ProtheusRestError(
            "Campo fornecedor é obrigatório.",
            code="PROTHEUS_SUPPLIER_PAYLOAD_INVALID",
            status_code=422,
            recoverable=False,
        )
    if not isinstance(raw, Mapping):
        raise ProtheusRestError(
            "Campo fornecedor deve ser um objeto JSON.",
            code="PROTHEUS_SUPPLIER_PAYLOAD_INVALID",
            status_code=422,
            recoverable=False,
        )

    lowered_keys = {str(k).strip().lower() for k in raw}
    if _FORBIDDEN_IDENTITY & lowered_keys:
        raise ProtheusRestError(
            "Identidade Protheus não pode ser enviada pelo cliente.",
            code="PROTHEUS_IDENTITY_CLIENT_FORBIDDEN",
            status_code=422,
            recoverable=False,
        )

    unknown = [str(k) for k in raw if str(k) not in EXPERIMENTAL_POST_ALLOWLIST]
    if unknown:
        raise ProtheusRestError(
            f"Campos não permitidos no fornecedor: {', '.join(sorted(unknown)[:10])}.",
            code="PROTHEUS_SUPPLIER_PAYLOAD_INVALID",
            status_code=422,
            recoverable=False,
        )

    out: dict[str, str] = {}
    for field, spec in EXPERIMENTAL_SUPPLIER_FIELD_SPECS.items():
        if field not in raw:
            if spec.get("required"):
                raise ProtheusRestError(
                    f"Campo obrigatório ausente: {field}.",
                    code="PROTHEUS_SUPPLIER_PAYLOAD_INVALID",
                    status_code=422,
                    recoverable=False,
                )
            continue
        value = raw[field]
        if value is None:
            continue
        out[field] = normalize_supplier_field_value(
            field, value, specs=EXPERIMENTAL_SUPPLIER_FIELD_SPECS
        )

    # Conditional rule (SX3 WHEN): CNAE somente quando TIPO é J ou X.
    if out.get("cnae_code") and out.get("person_type") == "F":
        raise ProtheusRestError(
            "Campo cnae_code não se aplica a pessoa física (person_type=F).",
            code="PROTHEUS_SUPPLIER_FIELD_CONDITIONAL",
            status_code=422,
            recoverable=False,
        )
    return out


def build_upstream_create_body_experimental(
    *, codusr: str, fornecedor: Mapping[str, str]
) -> dict[str, Any]:
    """Experimental upstream body — same canonical shape (codusr + objeto)."""
    return {
        "codusr": validate_codusr(codusr),
        "fornecedor": dict(fornecedor),
    }
