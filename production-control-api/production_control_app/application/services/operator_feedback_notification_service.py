"""Notificações Minha DELPI para Operator Feedback (C6).

Camada de ATENÇÃO apenas: dispara dispatch na Core API depois do impedimento
já persistido. Nunca replica domínio — a fonte de verdade continua sendo
operator_feedbacks / operator_feedback_materials / inbox PCP / fila urgente.

Gatilhos (os únicos da etapa — não notificar acknowledge/resolve/picked):
- feedback criado            → responsáveis pela Carga Máquina da filial;
- missing_material com itens → responsáveis pelo Alimentador da filial.

Destinatários: permissionCodes = seletor OR (função);
requiredPermissionCodes = filtro AND (filial). Sem o AND, alerta da filial
01 vazaria para quem só tem filial-02.

Best-effort absoluto: qualquer falha do gateway vira log — nunca propaga
para a criação do feedback nem para o cockpit do operador.
"""

from __future__ import annotations

import logging
from typing import Any

from production_control_app.core.security import BRANCH_VIEW_PERMISSIONS
from production_control_app.domain.operator_feedback import (
    OperatorFeedbackReason,
)

logger = logging.getLogger(__name__)

PCP_CATEGORY = "production_control_operator_feedback"
LINE_FEEDER_CATEGORY = "production_control_line_feeder_urgent"

_PC_MACHINE_LOAD_PERMISSION = "production-control.machine-load.view"
_PC_LINE_FEEDER_PERMISSION = "production-control.line-feeder.view"
_SOURCE_APP = "production-control"

#: Labels PT para os motivos conhecidos; fallback seguro para código cru.
_REASON_LABELS: dict[str, str] = {
    OperatorFeedbackReason.MISSING_MATERIAL.value: "Falta de matéria-prima",
}


class OperatorFeedbackNotificationService:
    """Monta os comandos de dispatch; não conhece httpx."""

    def __init__(self, *, gateway: Any | None) -> None:
        self._gateway = gateway

    def notify_feedback_created(
        self,
        *,
        feedback: dict[str, Any],
        material_count: int = 0,
    ) -> None:
        """Dispara notificações pós-persistência. Nunca levanta exceção."""
        if self._gateway is None:
            return
        branch = str(feedback.get("branch") or "").strip()
        production_order = str(feedback.get("production_order") or "").strip()
        operation_code = str(feedback.get("operation_code") or "").strip()
        work_center = str(feedback.get("reported_work_center") or "").strip()
        reason = str(feedback.get("reason_code") or "").strip()
        branch_permission = BRANCH_VIEW_PERMISSIONS.get(branch)
        if not branch_permission:
            logger.warning(
                "operator_feedback_notify_skipped feedback_id=%s branch=%s "
                "reason=unknown_branch",
                feedback.get("id"),
                branch,
            )
            return

        payloads = [
            self._pcp_payload(
                feedback=feedback,
                branch=branch,
                branch_permission=branch_permission,
                production_order=production_order,
                operation_code=operation_code,
                work_center=work_center,
                reason=reason,
            )
        ]
        if (
            reason == OperatorFeedbackReason.MISSING_MATERIAL.value
            and material_count > 0
        ):
            payloads.append(
                self._line_feeder_payload(
                    feedback=feedback,
                    branch=branch,
                    branch_permission=branch_permission,
                    production_order=production_order,
                    work_center=work_center,
                    material_count=material_count,
                )
            )

        for payload in payloads:
            self._dispatch(payload, feedback_id=feedback.get("id"))

    def _dispatch(self, payload: dict[str, Any], *, feedback_id: Any) -> None:
        try:
            self._gateway.dispatch(payload)
        except Exception:  # noqa: BLE001 — notificação nunca derruba o fato
            logger.warning(
                "operator_feedback_notification_failed feedback_id=%s "
                "category=%s",
                feedback_id,
                payload.get("category"),
                exc_info=True,
            )

    @staticmethod
    def _pcp_payload(
        *,
        feedback: dict[str, Any],
        branch: str,
        branch_permission: str,
        production_order: str,
        operation_code: str,
        work_center: str,
        reason: str,
    ) -> dict[str, Any]:
        reason_label = _REASON_LABELS.get(reason, reason or "impedimento")
        return {
            "title": "Novo impedimento na produção",
            "message": (
                f"A OP {production_order}, operação {operation_code}, "
                f"possui um novo impedimento informado pela bancada "
                f"{work_center}: {reason_label}."
            ),
            "type": "warning",
            "category": PCP_CATEGORY,
            "presentation": "text",
            "sourceApp": _SOURCE_APP,
            "permissionCodes": [_PC_MACHINE_LOAD_PERMISSION],
            "requiredPermissionCodes": [branch_permission],
            "action": {
                "type": "portal_route",
                "label": "Abrir Carga Máquina",
                "target": (
                    "/apps/production-control/machine-load"
                    f"?branch={branch}&locate={production_order}"
                ),
            },
            "metadata": {
                "event": "operator_feedback_created",
                "feedbackId": feedback.get("id"),
                "branch": branch,
                "productionOrder": production_order,
                "operationCode": operation_code,
            },
        }

    @staticmethod
    def _line_feeder_payload(
        *,
        feedback: dict[str, Any],
        branch: str,
        branch_permission: str,
        production_order: str,
        work_center: str,
        material_count: int,
    ) -> dict[str, Any]:
        plural = "material" if material_count == 1 else "materiais"
        return {
            "title": "Solicitação urgente de material",
            "message": (
                f"A bancada {work_center} informou falta de "
                f"{material_count} {plural} para a OP {production_order}."
            ),
            "type": "warning",
            "category": LINE_FEEDER_CATEGORY,
            "presentation": "text",
            "sourceApp": _SOURCE_APP,
            "permissionCodes": [_PC_LINE_FEEDER_PERMISSION],
            "requiredPermissionCodes": [branch_permission],
            "action": {
                "type": "portal_route",
                "label": "Abrir Alimentador de Linha",
                "target": f"/apps/production-control/line-feeder?branch={branch}",
            },
            "metadata": {
                "event": "operator_feedback_material_request_created",
                "feedbackId": feedback.get("id"),
                "branch": branch,
                "productionOrder": production_order,
                "materialCount": material_count,
            },
        }
