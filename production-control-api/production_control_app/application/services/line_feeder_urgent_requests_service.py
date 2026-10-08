"""Solicitações urgentes do Alimentador de Linha (C5).

Fila operacional dos materiais que o operador marcou como faltantes via
Operator Feedback — convive com as pick lists planejadas por corte sem se
misturar a elas (nenhuma pick plan é criada nem alterada aqui).

Regras de fronteira:
  * autorização = mesma do Alimentador: production-control.access + filial +
    production-control.line-feeder.view (padrão de LineFeederService);
  * autoria picked_by/delivered_by vem SOMENTE do JWT — nunca do body;
  * lifecycle delega ao OperatorFeedbackMaterialService (idempotente,
    transição condicional atômica, feedback resolved não transiciona);
  * material delivered NÃO resolve o feedback — quem encerra é o PCP;
  * CT atual é resolvido pela fila vigente (snapshot WORKING); a OP fora da
    fila fica marcada e continua visível — nada é apagado;
  * realtime é hint best-effort após a persistência;
  * nenhuma escrita no Protheus, nenhum toque em MES/Pulse/downtime.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from production_control_app.application.services.operator_feedback_material_service import (  # noqa: E501
    OperatorFeedbackMaterialService,
)
from production_control_app.core.security import PC_LINE_FEEDER_VIEW, can
from production_control_app.domain.errors import (
    OperatorFeedbackMaterialNotFound,
)
from production_control_app.domain.operator_feedback_material import (
    OperatorFeedbackMaterialStatus,
)
from production_control_app.domain.ports.machine_load_snapshot_repository import (  # noqa: E501
    MachineLoadSnapshotRepositoryPort,
)
from production_control_app.domain.ports.operator_feedback_material_repository import (  # noqa: E501
    OperatorFeedbackMaterialRepositoryPort,
)
from production_control_app.domain.services.branch_access_service import (
    BranchAccessService,
)
from production_control_app.domain.services.machine_load_snapshot_payload import (  # noqa: E501
    decode_snapshot_payload,
    payload_operations,
)
from production_control_app.domain.services.machine_load_withdrawal import (
    visible_operations,
    withdrawn_order_numbers,
)

logger = logging.getLogger(__name__)


def _text(value: Any) -> str:
    return str(value or "").strip()


def _actor(user: object | None) -> str:
    """Identificação estável do alimentador — mesma prioridade do PCP."""
    for attr in ("id", "username", "preferred_username", "email"):
        value = _text(getattr(user, attr, None))
        if value:
            return value[:120]
    return "line-feeder"


def _iso(value: Any) -> Any:
    return value.isoformat() if hasattr(value, "isoformat") else value


def _to_request_item(
    row: dict[str, Any], *, current_work_center: str | None
) -> dict[str, Any]:
    return {
        "id": row.get("id"),
        "feedbackId": row.get("feedback_id"),
        "productionOrder": row.get("feedback_production_order"),
        "operationCode": row.get("feedback_operation_code"),
        "productCode": row.get("product_code"),
        "description": row.get("description"),
        "unit": row.get("unit"),
        "openQty": row.get("open_qty"),
        "status": row.get("status"),
        "feedbackStatus": row.get("feedback_status"),
        "operatorCode": row.get("feedback_operator_code"),
        "operatorName": row.get("feedback_operator_name"),
        "note": row.get("feedback_note"),
        "reportedAt": _iso(row.get("feedback_created_at")),
        "reportedWorkCenter": row.get("feedback_reported_work_center"),
        "currentWorkCenter": current_work_center,
        "outOfQueue": current_work_center is None,
        "pickedAt": _iso(row.get("picked_at")),
        "deliveredAt": _iso(row.get("delivered_at")),
    }


class LineFeederUrgentRequestsService:
    def __init__(
        self,
        *,
        branch_access: BranchAccessService,
        materials: OperatorFeedbackMaterialRepositoryPort,
        lifecycle: OperatorFeedbackMaterialService,
        snapshots: MachineLoadSnapshotRepositoryPort,
        notify: Callable[..., None] | None = None,
    ) -> None:
        self._branch_access = branch_access
        self._materials = materials
        self._lifecycle = lifecycle
        self._snapshots = snapshots
        self._notify = notify

    def list_requests(
        self, user: object | None, *, branch: str
    ) -> dict[str, Any]:
        """Fila urgente da filial: pending|picked de feedbacks ainda ativos."""
        code = self._authorize(user, branch=branch)
        rows = self._materials.list_active_requests(branch=code)
        centers = self._current_work_centers(branch=code, rows=rows)
        items = [
            _to_request_item(
                row,
                current_work_center=centers.get(
                    (
                        _text(row.get("feedback_production_order")).upper(),
                        _text(row.get("feedback_operation_code"))
                        .lstrip("0")
                        or "0",
                    )
                ),
            )
            for row in rows
        ]
        pending = sum(
            1
            for item in items
            if item["status"] == OperatorFeedbackMaterialStatus.PENDING.value
        )
        return {
            "items": items,
            "summary": {
                "total": len(items),
                "pending": pending,
                "picked": len(items) - pending,
            },
        }

    def update_material_status(
        self,
        user: object | None,
        *,
        material_id: str,
        status: str,
    ) -> dict[str, Any]:
        """pending -> picked -> delivered. Autoria do JWT; filial autorizada
        pelo registro real — o UUID não abre a fila de outra filial."""
        wanted = _text(status).lower()
        if wanted not in (
            OperatorFeedbackMaterialStatus.PICKED.value,
            OperatorFeedbackMaterialStatus.DELIVERED.value,
        ):
            raise ValueError("Situação inválida para a solicitação urgente.")
        row = self._materials.get_material(str(material_id))
        if row is None:
            raise OperatorFeedbackMaterialNotFound(
                "Material do impedimento não encontrado."
            )
        code = self._authorize(
            user, branch=_text(row.get("feedback_branch"))
        )
        actor = _actor(user)
        if wanted == OperatorFeedbackMaterialStatus.PICKED.value:
            updated = self._lifecycle.mark_picked(str(material_id), picked_by=actor)
            reason = "material_picked"
        else:
            updated = self._lifecycle.mark_delivered(
                str(material_id), delivered_by=actor
            )
            reason = "material_delivered"
        self._notify_change(
            branch=code,
            reason=reason,
            material=updated,
            feedback=row,
        )
        merged = {
            key: row.get(key)
            for key in row
            if str(key).startswith("feedback_")
        }
        merged.update(updated)
        centers = self._current_work_centers(branch=code, rows=[merged])
        return {
            "item": _to_request_item(
                merged,
                current_work_center=centers.get(
                    (
                        _text(merged.get("feedback_production_order")).upper(),
                        _text(merged.get("feedback_operation_code"))
                        .lstrip("0")
                        or "0",
                    )
                ),
            )
        }

    def _authorize(self, user: object | None, *, branch: str) -> str:
        """Mesmo gate do Alimentador: acesso + filial + line-feeder.view."""
        code = self._branch_access.assert_valid_branch(branch)
        self._branch_access.assert_can_view_branch(user, code)
        if not can(user, PC_LINE_FEEDER_VIEW):
            raise PermissionError(
                "Você não tem permissão para o cockpit do alimentador de linha."
            )
        return code

    def _current_work_centers(
        self, *, branch: str, rows: list[dict[str, Any]]
    ) -> dict[tuple[str, str], str]:
        """Onde a OP/operação está AGORA na programação vigente (WORKING).

        reported_work_center é histórico do reporte; o destino da entrega é a
        fila atual. OP fora da fila não entra no mapa — a UI marca
        «fora da fila atual» sem apagar a solicitação.
        """
        try:
            snapshot = self._snapshots.get(branch=branch)
        except Exception:  # noqa: BLE001
            logger.warning("urgent_requests_snapshot_unavailable", exc_info=True)
            return {}
        if snapshot is None:
            return {}
        payload = decode_snapshot_payload(snapshot)
        operations = visible_operations(
            payload_operations(payload), withdrawn_order_numbers(payload)
        )
        centers: dict[tuple[str, str], str] = {}
        for item in operations:
            key = (
                _text(item.get("production_order")).upper(),
                _text(item.get("operation_code")).lstrip("0") or "0",
            )
            center = _text(item.get("work_center"))
            if center:
                centers[key] = center
        return centers

    def _notify_change(
        self,
        *,
        branch: str,
        reason: str,
        material: dict[str, Any],
        feedback: dict[str, Any],
    ) -> None:
        """Hint best-effort — a transição já persistiu; payload mínimo."""
        if self._notify is None:
            return
        try:
            self._notify(
                branch=branch,
                reason=reason,
                feedback={
                    "id": feedback.get("feedback_id") or feedback.get("id"),
                    "production_order": feedback.get("feedback_production_order"),
                    "operation_code": feedback.get("feedback_operation_code"),
                    "status": feedback.get("feedback_status"),
                },
            )
        except Exception:  # noqa: BLE001
            logger.warning(
                "operator_feedback_material_notify_failed", exc_info=True
            )
