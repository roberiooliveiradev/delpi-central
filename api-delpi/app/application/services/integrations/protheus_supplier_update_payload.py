"""Normalize PUT supplier fields and build the upstream array body.

PUT allowlist (PO decision, F3.3): every POST-cadastral field is editable
EXCEPT the fiscal document (tax_id) and the identity fields
(supplier_code/supplier_store). Upstream evidence for fields beyond
supplier_name/supplier_short_name is still pending TOTVS homologation —
the live-write gate PROTHEUS_SUPPLIER_UPDATE_ENABLED stays OFF until then.

Omitted keys are not sent (partial PUT). Explicit null/empty is rejected —
clear semantics remain TO_INVENTORY.
"""

from __future__ import annotations

import re
from typing import Any, Mapping

from app.application.services.integrations.protheus_supplier_create_payload import (
    SUPPLIER_FIELD_SPECS,
    normalize_supplier_field_value,
    validate_codusr,
)
from app.domain.integrations.protheus_rest import SUPPLIER_ID_PATTERN, ProtheusRestError

# Cadastral fields excluded from PUT: fiscal document (immutable here) and
# the store, which is part of the supplier identity (code+store).
_PUT_EXCLUDED = frozenset({"tax_id", "supplier_store"})

_UPDATE_SPECS: dict[str, dict[str, Any]] = {
    field: spec
    for field, spec in SUPPLIER_FIELD_SPECS.items()
    if field not in _PUT_EXCLUDED
}

# Fields that identify the supplier record or the ERP context — never writable.
_IMMUTABLE_FIELDS = frozenset(
    {
        "tax_id",
        "supplier_code",
        "supplier_store",
        "a2_cod",
        "a2_loja",
        "a2_filial",
    }
)

_FORBIDDEN_IDENTITY = frozenset(
    {"codusr", "user_id", "usr_id", "protheus_user_id", "supplier_id"}
)


def validate_supplier_id(supplier_id: str) -> str:
    normalized = str(supplier_id or "").strip()
    if not re.fullmatch(SUPPLIER_ID_PATTERN, normalized):
        raise ProtheusRestError(
            "Identificador de fornecedor inválido. Informe exatamente 8 dígitos "
            "(6 do código + 2 da loja).",
            code="PROTHEUS_SUPPLIER_ID_INVALID",
            status_code=422,
            recoverable=False,
        )
    return normalized


def normalize_supplier_update_fields(raw: Mapping[str, Any] | None) -> dict[str, str]:
    if isinstance(raw, list):
        raise ProtheusRestError(
            "A API DELPI recebe fornecedor como objeto; o array é montado no backend.",
            code="PROTHEUS_SUPPLIER_PAYLOAD_INVALID",
            status_code=422,
            recoverable=False,
        )
    if raw is None or not isinstance(raw, Mapping):
        raise ProtheusRestError(
            "Campo fornecedor deve ser um objeto JSON com os campos a alterar.",
            code="PROTHEUS_SUPPLIER_PAYLOAD_INVALID",
            status_code=422,
            recoverable=False,
        )

    lowered_keys = {str(k).strip().lower(): k for k in raw}
    forbidden = _FORBIDDEN_IDENTITY & lowered_keys.keys()
    if forbidden:
        raise ProtheusRestError(
            "Identidade do fornecedor ou do usuário não pode ser alterada nesta rota.",
            code="PROTHEUS_IDENTITY_CLIENT_FORBIDDEN",
            status_code=422,
            recoverable=False,
        )
    immutable = _IMMUTABLE_FIELDS & lowered_keys.keys()
    if immutable:
        raise ProtheusRestError(
            "Campo protegido da identidade cadastral não é editável: "
            + ", ".join(sorted(immutable))
            + ".",
            code="PROTHEUS_SUPPLIER_FIELD_IMMUTABLE",
            status_code=422,
            recoverable=False,
        )

    unknown = [str(k) for k in raw.keys() if str(k) not in _UPDATE_SPECS]
    if unknown:
        raise ProtheusRestError(
            "Campos não comprovados para alteração: "
            + ", ".join(sorted(unknown)[:10])
            + ".",
            code="PROTHEUS_SUPPLIER_FIELD_NOT_EDITABLE",
            status_code=422,
            recoverable=False,
        )

    out: dict[str, str] = {}
    for field in _UPDATE_SPECS:
        if field not in raw:
            continue
        value = raw[field]
        if value is None or (isinstance(value, str) and value.strip() == ""):
            raise ProtheusRestError(
                f"Limpeza explícita de {field} não está homologada. Omita o campo para preservá-lo.",
                code="PROTHEUS_SUPPLIER_CLEAR_NOT_SUPPORTED",
                status_code=422,
                recoverable=False,
            )
        out[field] = normalize_supplier_field_value(field, value)

    if not out:
        raise ProtheusRestError(
            "Informe ao menos um campo comprovado para alteração.",
            code="PROTHEUS_SUPPLIER_PAYLOAD_INVALID",
            status_code=422,
            recoverable=False,
        )
    return out


def build_upstream_update_body(*, codusr: str, fields: Mapping[str, str]) -> dict[str, Any]:
    return {
        "codusr": validate_codusr(codusr),
        "fornecedor": [dict(fields)],
    }
