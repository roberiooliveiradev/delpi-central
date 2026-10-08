"""Problema de Processo no cockpit público — orquestração da P2.

Confiança: o operador só informa OP/operação/motivo (+ ferramenta, material e
nota opcionais). Identidade, filial e posto vêm SEMPRE da bench session; o
contexto da OP é congelado da fila PUBLISHED (mesma fonte do cockpit — nunca
WORKING nem TOTVS) e os materiais vinculados vêm da SD4 oficial.

Degradação: a falha da consulta SD4 NÃO bloqueia o reporte — a solicitação é
criada com ``materialsSnapshotAvailable: false``. Já a indisponibilidade do
Requests API falha a operação: a solicitação é o objetivo, não camada de
atenção — nunca se devolve sucesso falso nem se persiste réplica local.

Segurança de enumeração: operação inexistente e operação publicada em outro
posto recebem a MESMA resposta 404 — o link anônimo não vira oráculo de fila.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from production_control_app.application.services.machine_load_service import (
    MachineLoadService,
)
from production_control_app.domain.errors import SnapshotNotFound

logger = logging.getLogger(__name__)

_PROCESS_ISSUE_SOURCE_APP = "production-control"
_PROCESS_ISSUE_TYPE_CODE = "process-issue"
_CONFIRM_MESSAGE = "Solicitação enviada para Processos."

_OPERATION_UNAVAILABLE = (
    "Esta operação não está disponível neste posto na fila publicada."
)


def _text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _to_material_snapshot(row: dict[str, Any]) -> dict[str, Any]:
    """Item SD4 → snapshot camelCase do contrato process-issue.

    Somente contexto para o analista — nunca base para movimentação de
    estoque."""
    return {
        "productCode": _text(row.get("product_code")),
        "description": _text(row.get("description")),
        "unit": _text(row.get("unit")),
        "originalQty": row.get("original_qty") or 0,
        "openQty": row.get("open_qty") or 0,
        "consumedQty": row.get("consumed_qty") or 0,
    }


class PublicProcessIssueService:
    def __init__(
        self,
        *,
        run_service: Any,
        machine_load: MachineLoadService,
        requests_gateway: Any,
        operation_materials: Any | None = None,
    ) -> None:
        self._run_service = run_service
        self._machine_load = machine_load
        self._requests_gateway = requests_gateway
        # Snapshot SD4 best-effort: PublicOperationMaterialsService.list_for_feedback
        self._operation_materials = operation_materials

    def report(
        self,
        *,
        session_token: str | None,
        production_order: str,
        operation_code: str,
        issue_code: str,
        idempotency_key: str,
        tool_code: str | None = None,
        material_code: str | None = None,
        note: str | None = None,
    ) -> dict[str, Any]:
        session = self._run_service.resolve_bench_session(session_token)
        branch = str(session.get("branch") or "").strip()
        work_center = str(session.get("work_center") or "").strip()
        operator_code = str(session.get("operator_code") or "").strip()
        operator_name = str(session.get("operator_name") or "").strip()

        context = self._machine_load.public_operation_process_issue_context(
            branch=branch,
            production_order=production_order,
            operation_code=operation_code,
        )
        # Ausência na PUBLISHED e publicação em outro posto: mesma resposta —
        # um link anônimo não pode mapear a fila dos outros centros.
        if context is None or context.get("work_center") != work_center:
            raise SnapshotNotFound(_OPERATION_UNAVAILABLE)

        materials, materials_available = self._materials_snapshot(
            branch=branch, context=context
        )

        payload = {
            "source": "operator_cockpit",
            "reportedAt": datetime.now(timezone.utc).isoformat(),
            "issue": {
                "code": str(issue_code or "").strip(),
                "reportedToolCode": _text(tool_code),
                "reportedMaterialCode": _text(material_code),
                "note": _text(note),
            },
            "operator": {
                "code": operator_code,
                "name": operator_name,
            },
            "operation": {
                "productionOrder": context["production_order"],
                "operationCode": context["operation_code"],
                "description": _text(context.get("operation_description")),
                "reportedWorkCenter": work_center,
                "workCenterName": _text(context.get("work_center_name")),
                "productCode": _text(context.get("product_code")),
                "productDescription": _text(context.get("product_description")),
                "unit": _text(context.get("unit")),
                "paProductCode": _text(context.get("pa_product_code")),
                "paProductDescription": _text(
                    context.get("pa_product_description")
                ),
                "toolSnapshot": context.get("tool") or "",
                "resource": _text(context.get("resource")),
                "plannedQty": context.get("planned_qty"),
                "pendingQty": context.get("pending_qty"),
                "operationPendingQty": context.get("operation_pending_qty"),
                "scheduledDate": context.get("scheduled_date"),
                "scheduledStartTime": context.get("scheduled_start_time"),
                "scheduledEndDate": context.get("scheduled_end_date"),
                "scheduledEndTime": context.get("scheduled_end_time"),
                "dueDate": context.get("due_date"),
            },
            "materialsSnapshotAvailable": materials_available,
            "materials": materials,
        }

        # Identidade externa estável — o operador não possui conta Minha DELPI;
        # quem trata a solicitação segue sob RBAC de filial no Requests API.
        external_id = f"operator:{branch}:{operator_code}"
        result = self._requests_gateway.create_request(
            body={
                "sourceApp": _PROCESS_ISSUE_SOURCE_APP,
                "typeCode": _PROCESS_ISSUE_TYPE_CODE,
                "branch": branch,
                "priority": "normal",
                "requester": {
                    "externalId": external_id,
                    "name": operator_name or "Operador",
                },
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
        """Congela os materiais SD4 vinculados; falha não bloqueia o reporte."""
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
                "process_issue_materials_unavailable order=%s op=%s",
                context.get("production_order"),
                context.get("operation_code"),
                exc_info=True,
            )
            return [], False
        return [_to_material_snapshot(item) for item in items], True
