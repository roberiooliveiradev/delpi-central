"""Validate and normalize POST supplier payload (REST field names → upstream shape)."""

from __future__ import annotations

import re
from typing import Any, Mapping

from app.domain.integrations.protheus_rest import ProtheusRestError

# Max lengths from SA2 SX3 (§44.3) for REST field names in the POST contract example.
# Shared canonical source — PUT validation reuses these specs per field.
SUPPLIER_FIELD_SPECS: dict[str, dict[str, Any]] = {
    "supplier_store": {"max": 2, "digits": True, "required": True, "label": "Loja"},
    "person_type": {"max": 1, "enum": frozenset({"F", "J", "X"})},
    "tax_id": {"max": 14, "digits": True},
    "supplier_name": {"max": 50},
    "supplier_short_name": {"max": 20},
    "address": {"max": 40},
    "district": {"max": 20},
    "postal_code": {"max": 8, "digits": True},
    "state": {"max": 2, "upper": True},
    "city": {"max": 25},
    "city_code": {"max": 5, "digits": True},
    "area_code": {"max": 3, "digits": True},
    "phone": {"max": 50},
    "state_registration": {"max": 18},
    "municipal_registration": {"max": 18},
    "contact_name": {"max": 15},
    "email": {"max": 50, "email": True},
    "payment_condition_code": {
        "max": 3,
        "required": True,
        "label": "Condição de pagamento",
    },
    "country_code": {"max": 3},
    "bacen_country_code": {
        "max": 5,
        "digits": True,
        "required": True,
        "label": "País (BACEN)",
    },
    "accounting_account": {
        "max": 20,
        "required": True,
        "label": "Conta contábil",
    },
    "financial_nature_code": {
        "max": 10,
        "required": True,
        "label": "Natureza financeira",
    },
    "rohs_indicator": {
        "max": 1,
        "enum": frozenset({"S", "N", ""}),
        "required": True,
        "label": "Indicador ROHS",
    },
    "payment_method_code": {
        "max": 2,
        "required": True,
        "label": "Forma de pagamento",
    },
    # --- X4.FIELDS.E3 — campos promovidos ao contrato público -------------
    # Persistência comprovada em homologação DELPI_TST01 (E2, 2026-10-23,
    # doc X4-FIELDS-E2-*). Specs SX3 idênticas ao protótipo E1 — fonte
    # canônica única (não duplicar no módulo experimental).
    # --- endereço ---------------------------------------------------------
    "address_number": {"max": 6, "digits": True},
    "po_box": {"max": 5},
    # --- fiscal / tributário ----------------------------------------------
    "icms_contributor": {"max": 1, "enum": frozenset({"", "1", "2"})},
    "simples_nacional": {"max": 1, "enum": frozenset({"", "1", "2"})},
    "cnae_code": {"max": 9, "digits": True, "conditional": "person_type_jx"},
    "legal_entity_type": {"max": 1, "enum": frozenset({"", "1", "2", "3", "4", "5"})},
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
    # --- contato ----------------------------------------------------------
    "commercial_contact_name": {"max": 15},
    "fax": {"max": 15, "digits": True},
    "website": {"max": 30},
    "responsible_name": {"max": 45},
    # --- comercial / referências ------------------------------------------
    "risk_code": {"max": 3},
    "swift_code": {"max": 30, "upper": True},
    "purchase_price_table_code": {"max": 3},
    "carrier_code": {"max": 6},
    "segment_code": {"max": 6},
    "administrator_code": {"max": 3},
    "linked_customer_code": {"max": 6},
    "linked_customer_store": {"max": 2},
    "linked_employee_code": {"max": 6},
}

_ALLOWED_FIELDS = frozenset(SUPPLIER_FIELD_SPECS)
_DIGITS_RE = re.compile(r"^\d*$")
_CODUSR_RE = re.compile(r"^\d{6}$")


def validate_codusr(value: str) -> str:
    normalized = str(value or "").strip()
    if not _CODUSR_RE.fullmatch(normalized):
        raise ProtheusRestError(
            "Identidade Protheus do usuário inválida para codusr (esperado 6 dígitos).",
            code="PROTHEUS_IDENTITY_INVALID",
            status_code=422,
            recoverable=False,
        )
    return normalized


def normalize_supplier_fields(raw: Mapping[str, Any] | None) -> dict[str, str]:
    """Normalize client fornecedor object. Rejects unknown keys and client-supplied identity."""
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

    forbidden_identity = {"codusr", "user_id", "usr_id", "protheus_user_id"}
    for key in raw:
        lowered = str(key).strip().lower()
        if lowered in forbidden_identity:
            raise ProtheusRestError(
                "Identidade Protheus não pode ser enviada pelo cliente.",
                code="PROTHEUS_IDENTITY_CLIENT_FORBIDDEN",
                status_code=422,
                recoverable=False,
            )

    unknown = [str(k) for k in raw.keys() if str(k) not in _ALLOWED_FIELDS]
    if unknown:
        raise ProtheusRestError(
            f"Campos não permitidos no fornecedor: {', '.join(sorted(unknown)[:10])}.",
            code="PROTHEUS_SUPPLIER_PAYLOAD_INVALID",
            status_code=422,
            recoverable=False,
        )

    # Aggregate validation (X4.PROD-C1.R6): collect every missing/invalid
    # field before failing so callers receive the complete correction list —
    # validation never reaches token, tracking or the upstream POST.
    field_errors: list[dict[str, str]] = []
    out: dict[str, str] = {}
    for field, spec in SUPPLIER_FIELD_SPECS.items():
        value = raw.get(field)
        present = value is not None and str(value).strip() != ""
        if spec.get("required") and not present:
            field_errors.append(
                {
                    "field": field,
                    "code": "missing_required",
                    "message": (
                        f"Campo obrigatório ausente: {_field_label(spec, field)}."
                    ),
                }
            )
            continue
        if value is None:
            continue
        try:
            out[field] = normalize_supplier_field_value(field, value)
        except ProtheusRestError as exc:
            field_errors.append(
                {"field": field, "code": "invalid_value", "message": exc.message}
            )

    # Conditional rules (SX3 WHEN): cnae_code only applies to person_type
    # J or X — same rule the experimental normalizer proved in E1/E2.
    for field, value in out.items():
        spec = SUPPLIER_FIELD_SPECS[field]
        if (
            spec.get("conditional") == "person_type_jx"
            and value
            and out.get("person_type") == "F"
        ):
            field_errors.append(
                {
                    "field": field,
                    "code": "conditional",
                    "message": (
                        f"Campo {field} não se aplica a pessoa física "
                        "(person_type=F)."
                    ),
                }
            )

    if field_errors:
        codes = {entry["code"] for entry in field_errors}
        if codes == {"missing_required"}:
            top_code = "SUPPLIER_REQUIRED_FIELDS_MISSING"
        elif codes == {"conditional"}:
            top_code = "PROTHEUS_SUPPLIER_FIELD_CONDITIONAL"
        else:
            top_code = "PROTHEUS_SUPPLIER_PAYLOAD_INVALID"
        raise ProtheusRestError(
            "Preencha os campos obrigatórios do fornecedor para continuar."
            if top_code == "SUPPLIER_REQUIRED_FIELDS_MISSING"
            else "O cadastro do fornecedor contém campos obrigatórios "
            "ausentes ou valores inválidos.",
            code=top_code,
            status_code=422,
            recoverable=False,
            fields=field_errors,
        )
    return out


def _field_label(spec: Mapping[str, Any], field: str) -> str:
    label = spec.get("label")
    return str(label) if label else field


def normalize_supplier_field_value(
    field: str,
    value: Any,
    *,
    specs: Mapping[str, dict[str, Any]] | None = None,
) -> str:
    """Canonical per-field normalization shared by POST and PUT.

    ``specs`` defaults to the published contract allowlist; experiments
    (X4.FIELDS.E1) may inject a widened spec table without touching the
    public contract.
    """
    spec = (specs or SUPPLIER_FIELD_SPECS)[field]
    # Preserve leading zeros — never cast numeric types back after stringify of ints.
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        raise ProtheusRestError(
            f"Campo {field} deve ser string para preservar zeros à esquerda.",
            code="PROTHEUS_SUPPLIER_PAYLOAD_INVALID",
            status_code=422,
            recoverable=False,
        )
    text = str(value).strip()

    if spec.get("upper"):
        text = text.upper()
    if spec.get("digits") and text and not _DIGITS_RE.fullmatch(text):
        raise ProtheusRestError(
            f"Campo {field} deve conter apenas dígitos.",
            code="PROTHEUS_SUPPLIER_PAYLOAD_INVALID",
            status_code=422,
            recoverable=False,
        )
    allowed = spec.get("enum")
    if allowed is not None and text not in allowed:
        raise ProtheusRestError(
            f"Campo {field} com valor inválido.",
            code="PROTHEUS_SUPPLIER_PAYLOAD_INVALID",
            status_code=422,
            recoverable=False,
        )
    max_len = int(spec["max"])
    if len(text) > max_len:
        raise ProtheusRestError(
            f"Campo {field} excede o tamanho máximo ({max_len}).",
            code="PROTHEUS_SUPPLIER_PAYLOAD_INVALID",
            status_code=422,
            recoverable=False,
        )
    if field == "supplier_store" and not re.fullmatch(r"^\d{2}$", text):
        raise ProtheusRestError(
            "supplier_store deve ter exatamente 2 dígitos.",
            code="PROTHEUS_SUPPLIER_PAYLOAD_INVALID",
            status_code=422,
            recoverable=False,
        )
    if spec.get("email") and text and "@" not in text:
        raise ProtheusRestError(
            "Campo email inválido.",
            code="PROTHEUS_SUPPLIER_PAYLOAD_INVALID",
            status_code=422,
            recoverable=False,
        )
    if spec.get("required") and not text:
        raise ProtheusRestError(
            f"Campo obrigatório ausente: {field}.",
            code="PROTHEUS_SUPPLIER_PAYLOAD_INVALID",
            status_code=422,
            recoverable=False,
        )
    return text


def build_upstream_create_body(*, codusr: str, fornecedor: Mapping[str, str]) -> dict[str, Any]:
    return {
        "codusr": validate_codusr(codusr),
        "fornecedor": dict(fornecedor),
    }
