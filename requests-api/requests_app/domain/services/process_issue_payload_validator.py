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

# Origem do cockpit do operador (fluxo original P2).
PROCESS_ISSUE_SOURCE = "operator_cockpit"
# Origem autenticada do Portal PCP — o analista abre a solicitacao pela Carga
# Maquina com identidade de usuario real (criacao autenticada, nao S2S).
PCP_PORTAL_SOURCE = "pcp_portal"
# Origem autenticada do Delpi MES — triagem gerencial de paradas encaminha
# process-issue com identidade de usuario real (Bearer), nunca S2S fabricada.
DELPI_MES_SOURCE = "delpi_mes"
PROCESS_ISSUE_SOURCES = frozenset(
    {PROCESS_ISSUE_SOURCE, PCP_PORTAL_SOURCE, DELPI_MES_SOURCE}
)

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

        source = str(payload.get("source") or "").strip()
        if source not in PROCESS_ISSUE_SOURCES:
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

        if source == PROCESS_ISSUE_SOURCE:
            operator = payload.get("operator")
            if not isinstance(operator, dict):
                raise _invalid("operator", "Identidade do operador é obrigatória.")
            _require_text(operator, "code")
        else:
            # pcp_portal: o autoridade da identidade é o usuário autenticado
            # (created_by do request); o bloco requester é o espelho do
            # snapshot para exibição — nunca substitui o principal.
            requester = payload.get("requester")
            if not isinstance(requester, dict):
                raise _invalid("requester", "Identidade do solicitante é obrigatória.")
            _require_text(requester, "name")
            if len(str(requester.get("name") or "").strip()) > 150:
                raise _invalid("requester.name", "requester.name excede 150 caracteres.")

        operation = payload.get("operation")
        if source == DELPI_MES_SOURCE:
            # Parada MES pode não ter OP vinculada — a âncora do problema é o
            # bloco mesDowntime; operation é opcional e, quando presente,
            # segue o mesmo contrato das demais origens.
            mes_downtime = payload.get("mesDowntime")
            if not isinstance(mes_downtime, dict):
                raise _invalid(
                    "mesDowntime", "Contexto da parada MES é obrigatório."
                )
            for field in ("downtimeId", "branch", "workCenter"):
                _require_text(mes_downtime, field)
            if operation is not None:
                if not isinstance(operation, dict):
                    raise _invalid(
                        "operation", "Contexto da operação inválido."
                    )
                for field in (
                    "productionOrder",
                    "operationCode",
                    "reportedWorkCenter",
                ):
                    _require_text(operation, field)
        else:
            if not isinstance(operation, dict):
                raise _invalid(
                    "operation", "Contexto da operação é obrigatório."
                )
            for field in (
                "productionOrder",
                "operationCode",
                "reportedWorkCenter",
            ):
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
