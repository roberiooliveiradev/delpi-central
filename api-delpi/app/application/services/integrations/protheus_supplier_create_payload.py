"""Validate and normalize POST supplier payload (REST field names → upstream shape)."""

from __future__ import annotations

import re
from typing import Any, Mapping

from app.domain.integrations.protheus_rest import ProtheusRestError

# Max lengths from SA2 SX3 (§44.3) for REST field names in the POST contract example.
# Shared canonical source — PUT validation reuses these specs per field.
SUPPLIER_FIELD_SPECS: dict[str, dict[str, Any]] = {
    "supplier_store": {"max": 2, "digits": True, "required": True},
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
    "payment_condition_code": {"max": 3},
    "country_code": {"max": 3},
    "bacen_country_code": {"max": 5, "digits": True},
    "accounting_account": {"max": 20},
    "financial_nature_code": {"max": 10},
    "rohs_indicator": {"max": 1, "enum": frozenset({"S", "N", ""})},
    "payment_method_code": {"max": 2},
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

    out: dict[str, str] = {}
    for field, spec in SUPPLIER_FIELD_SPECS.items():
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
            if spec.get("required"):
                raise ProtheusRestError(
                    f"Campo obrigatório ausente: {field}.",
                    code="PROTHEUS_SUPPLIER_PAYLOAD_INVALID",
                    status_code=422,
                    recoverable=False,
                )
            continue
        out[field] = normalize_supplier_field_value(field, value)

    return out


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
