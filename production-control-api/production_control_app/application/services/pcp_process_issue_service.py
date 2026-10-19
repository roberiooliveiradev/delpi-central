"""Problema de Processo pelo Portal PCP — extensão do fluxo existente.

Mesma solicitação process-issue, mesmo catálogo, mesmo workflow do
departamento de Processos — o que muda é a ORIGEM: em vez do link público do
cockpit (operador, fila PUBLISHED, identidade externa operator:*), o
analista autenticado abre a solicitação pela Carga Máquina (fila WORKING) e
a criação chega ao Requests API pelo contrato autenticado POST
/v1/requests com o Bearer do próprio usuário — created_by = usuário real,
notificações e trilha de auditoria intactas, sem identidade externa
fictícia e sem bypass de RBAC.

Autorização (fail-closed, sempre backend):
- production-control.access + production-control.view.filial-XX +
  production-control.machine-load.view (mesmo gate da leitura da carga);
- my-requests.process-issue.create conferida aqui E reaplicada pelo
  Requests API sobre o JWT encaminhado;
- o usuário precisa de access_token no principal — chamadas sem Bearer
  de usuário (ex.: service principal) são negadas.

Contexto: revalidado na fila WORKING no momento do envio. Operação retirada
ou movida para outro centro → conflito controlado; inexistente → 404 —
nunca se grava contexto obsoleto em silêncio.

Degradação: falha da consulta SD4 NÃO bloqueia a solicitação
(materialsSnapshotAvailable: false). Indisponibilidade do Requests API
falha a operação — a criação é o objetivo, nunca se devolve sucesso falso.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from production_control_app.application.services.machine_load_service import (
    MachineLoadService,
)
from production_control_app.core.security import (
    REQUESTS_PROCESS_ISSUE_CREATE,
    can,
)

logger = logging.getLogger(__name__)

_PROCESS_ISSUE_SOURCE_APP = "production-control"
_PROCESS_ISSUE_TYPE_CODE = "process-issue"
_PROCESS_ISSUE_SOURCE = "pcp_portal"
_CONFIRM_MESSAGE = "Solicitação enviada para Processos com sucesso."


def _text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _to_material_snapshot(row: dict[str, Any]) -> dict[str, Any]:
    """Item SD4 → snapshot camelCase do contrato process-issue (informativo)."""
    return {
        "productCode": _text(row.get("product_code")),
        "description": _text(row.get("description")),
        "unit": _text(row.get("unit")),
        "originalQty": row.get("original_qty") or 0,
        "openQty": row.get("open_qty") or 0,
        "consumedQty": row.get("consumed_qty") or 0,
    }


class PcpProcessIssueService:
    def __init__(
        self,
        *,
        machine_load: MachineLoadService,
        requests_gateway: Any,
        operation_materials: Any | None = None,
    ) -> None:
        self._machine_load = machine_load
        self._requests_gateway = requests_gateway
        # Snapshot SD4 best-effort: PublicOperationMaterialsService.list_for_feedback
        self._operation_materials = operation_materials

    def report(
        self,
        user: object | None,
        *,
        branch: str,
        work_center: str,
        production_order: str,
        operation_code: str,
        issue_code: str,
        idempotency_key: str,
        tool_code: str | None = None,
        material_code: str | None = None,
        note: str | None = None,
    ) -> dict[str, Any]:
        if not can(user, REQUESTS_PROCESS_ISSUE_CREATE):
            raise PermissionError(
                "Você não tem permissão para criar solicitações de processo."
            )
        if getattr(user, "principal_type", None) == "service":
            raise PermissionError(
                "Apenas usuários autenticados podem solicitar correção."
            )
        access_token = str(getattr(user, "access_token", None) or "").strip()
        if not access_token:
            raise PermissionError(
                "Sessão inválida para registrar a solicitação."
            )

        # Revalida a identidade completa na fila WORKING vigente — inclui o
        # gate de filial + machine-load.view do usuário.
        context = self._machine_load.pcp_operation_process_issue_context(
            user,
            branch=branch,
            work_center=work_center,
            production_order=production_order,
            operation_code=operation_code,
        )

        materials, materials_available = self._materials_snapshot(
            branch=str(branch or "").strip(), context=context
        )

        payload = {
            "source": _PROCESS_ISSUE_SOURCE,
            "reportedAt": datetime.now(timezone.utc).isoformat(),
            "issue": {
                "code": str(issue_code or "").strip(),
                "reportedToolCode": _text(tool_code),
                "reportedMaterialCode": _text(material_code),
                "note": _text(note),
            },
            "requester": {
                "name": str(getattr(user, "name", "") or "").strip() or "Analista PCP",
            },
            "operation": {
                "productionOrder": context["production_order"],
                "operationCode": context["operation_code"],
                "description": _text(context.get("operation_description")),
                "reportedWorkCenter": context["work_center"],
                "workCenterName": _text(context.get("work_center_name")),
                "productCode": _text(context.get("product_code")),
                "productDescription": _text(context.get("product_description")),
                "paProductCode": _text(context.get("pa_product_code")),
                "paProductDescription": _text(
                    context.get("pa_product_description")
                ),
                "toolSnapshot": context.get("tool") or "",
                "resource": _text(context.get("resource")),
            },
            "materialsSnapshotAvailable": materials_available,
            "materials": materials,
        }

        result = self._requests_gateway.create_request_as_user(
            access_token=access_token,
            body={
                "sourceApp": _PROCESS_ISSUE_SOURCE_APP,
                "typeCode": _PROCESS_ISSUE_TYPE_CODE,
                # O tipo process-issue exige filial (branch_scope=required) e
                # o Requests API confere my-requests.view.filial-XX do JWT.
                "branch": str(branch or "").strip(),
                "payload": payload,
            },
            idempotency_key=idempotency_key,
        )
        return {
            "requestId": result.get("id"),
            "requestNumber": result.get("request_number"),
            "status": result.get("status"),
            "message": _CONFIRM_MESSAGE,
        }

    def _materials_snapshot(
        self, *, branch: str, context: dict[str, Any]
    ) -> tuple[list[dict[str, Any]], bool]:
        """Congela os materiais SD4 vinculados; falha não bloqueia o envio."""
        if self._operation_materials is None:
            return [], False
        try:
            items = self._operation_materials.list_for_feedback(
                branch=branch,
                production_order=context["production_order"],
                operation_code=context["operation_code"],
            )
        except Exception:  # noqa: BLE001 — degradação explícita do contrato
            logger.warning(
                "pcp_process_issue_materials_unavailable order=%s op=%s",
                context.get("production_order"),
                context.get("operation_code"),
                exc_info=True,
            )
            return [], False
        return [_to_material_snapshot(item) for item in items], True
