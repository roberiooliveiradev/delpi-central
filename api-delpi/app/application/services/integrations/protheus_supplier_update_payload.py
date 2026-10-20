"""Normalize PUT supplier fields and build the upstream array body.

Proven editable fields (REST contract example): supplier_name, supplier_short_name.
Other POST fields stay out of the allowlist until the upstream owner confirms them.
Omitted keys are not sent. Explicit null/empty is rejected (clear semantics TO_INVENTORY).
"""

from __future__ import annotations

import re
from typing import Any, Mapping

from app.application.services.integrations.protheus_supplier_create_payload import (
    validate_codusr,
)
from app.domain.integrations.protheus_rest import SUPPLIER_ID_PATTERN, ProtheusRestError

_UPDATE_SPECS: dict[str, dict[str, Any]] = {
    "supplier_name": {"max": 50},
    "supplier_short_name": {"max": 20},
}

_FORBIDDEN_IDENTITY = frozenset(
    {"codusr", "user_id", "usr_id", "protheus_user_id", "supplier_id", "a2_cod", "a2_loja"}
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

    for key in raw:
        if str(key).strip().lower() in _FORBIDDEN_IDENTITY:
            raise ProtheusRestError(
                "Identidade do fornecedor ou do usuário não pode ser alterada nesta rota.",
                code="PROTHEUS_IDENTITY_CLIENT_FORBIDDEN",
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
    for field, spec in _UPDATE_SPECS.items():
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
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            raise ProtheusRestError(
                f"Campo {field} deve ser string.",
                code="PROTHEUS_SUPPLIER_PAYLOAD_INVALID",
                status_code=422,
                recoverable=False,
            )
        text = str(value).strip()
        max_len = int(spec["max"])
        if len(text) > max_len:
            raise ProtheusRestError(
                f"Campo {field} excede o tamanho máximo ({max_len}).",
                code="PROTHEUS_SUPPLIER_PAYLOAD_INVALID",
                status_code=422,
                recoverable=False,
            )
        out[field] = text

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
