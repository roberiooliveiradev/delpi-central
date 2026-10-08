"""Validação de aplicação do payload process-issue (P2).

O form_schema do tipo é propositalmente permissivo (o snapshot evolui sem
migration); o contrato mínimo é validado aqui — Requests API é a autoridade
final. Campos legitimamente ausentes (PA, ferramenta, materiais, nota) não
são obrigatórios.
"""

from __future__ import annotations

from typing import Any

from requests_app.application.errors import ApplicationError
from requests_app.domain.ports.payload_validator_port import PayloadValidatorPort
from requests_app.domain.process_issue_catalog import (
    ISSUE_CODES,
    PROCESS_ISSUE_TYPE_CODE,
)

PROCESS_ISSUE_SOURCE = "operator_cockpit"

_TEXT_LIMITS: dict[str, int] = {
    "reportedToolCode": 60,
    "reportedMaterialCode": 60,
    "note": 500,
}


def _invalid(field: str, detail: str) -> ApplicationError:
    return ApplicationError(
        code="payload_invalid", status_code=422, field=field, detail=detail
    )


def _require_text(node: dict[str, Any], field: str) -> None:
    if not str(node.get(field) or "").strip():
        raise _invalid(field, f"{field} é obrigatório.")


def _optional_text(node: dict[str, Any], field: str) -> None:
    value = node.get(field)
    if value is None:
        return
    if not isinstance(value, str):
        raise _invalid(field, f"{field} deve ser texto.")
    limit = _TEXT_LIMITS.get(field)
    if limit is not None and len(value.strip()) > limit:
        raise _invalid(field, f"{field} excede {limit} caracteres.")


class ProcessIssuePayloadValidator(PayloadValidatorPort):
    type_code = PROCESS_ISSUE_TYPE_CODE

    def validate(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise ApplicationError(code="payload_required", status_code=422)

        if str(payload.get("source") or "").strip() != PROCESS_ISSUE_SOURCE:
            raise _invalid("source", "Origem do problema de processo inválida.")
        _require_text(payload, "reportedAt")

        issue = payload.get("issue")
        if not isinstance(issue, dict):
            raise _invalid("issue", "Bloco issue é obrigatório.")
        code = str(issue.get("code") or "").strip()
        if code not in ISSUE_CODES:
            raise _invalid("issue.code", "Motivo de problema de processo desconhecido.")
        for field in _TEXT_LIMITS:
            _optional_text(issue, field)

        operator = payload.get("operator")
        if not isinstance(operator, dict):
            raise _invalid("operator", "Identidade do operador é obrigatória.")
        _require_text(operator, "code")

        operation = payload.get("operation")
        if not isinstance(operation, dict):
            raise _invalid("operation", "Contexto da operação é obrigatório.")
        for field in ("productionOrder", "operationCode", "reportedWorkCenter"):
            _require_text(operation, field)

        available = payload.get("materialsSnapshotAvailable")
        if available is not None and not isinstance(available, bool):
            raise _invalid(
                "materialsSnapshotAvailable", "materialsSnapshotAvailable deve ser booleano."
            )
        materials = payload.get("materials")
        if materials is not None:
            if not isinstance(materials, list) or not all(
                isinstance(item, dict) for item in materials
            ):
                raise _invalid("materials", "materials deve ser uma lista de itens.")
        return payload
