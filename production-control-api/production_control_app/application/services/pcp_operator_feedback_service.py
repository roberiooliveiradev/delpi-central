"""Operator Feedback no Portal PCP — orquestração autenticada (C4).

Inbox + tratativa dos impedimentos reportados pelo cockpit do operador.
Autorização segue a Carga Máquina: production-control.access +
production-control.machine-load.view + permissão da filial — sem RBAC paralelo.

Regras de fronteira:
  * lifecycle NUNCA é reimplementado aqui — acknowledge/resolve delegam ao
    OperatorFeedbackService (C1), que é idempotente e atômico;
  * a identidade funcional é branch + OP + operação — reported_work_center é
    histórico e não limita a inbox (a OP pode ter sido transferida);
  * autoria PCP (acknowledged_by/resolved_by) vem SOMENTE do JWT resolvido —
    o body nunca é autoridade;
  * realtime é hint best-effort — a persistência já aconteceu quando o
    broadcast é tentado;
  * nada aqui toca MES: sem pause/stop/downtime, sem Pulse, sem mutação da
    Carga Máquina.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from production_control_app.application.services.operator_feedback_service import (
    OperatorFeedbackService,
)
from production_control_app.core.security import PC_MACHINE_LOAD_VIEW, can
from production_control_app.domain.errors import OperatorFeedbackNotFound
from production_control_app.domain.operator_feedback import OperatorFeedbackStatus
from production_control_app.domain.services.branch_access_service import (
    BranchAccessService,
)

logger = logging.getLogger(__name__)

_RESOLUTION_NOTE_MAX = 500


def _iso(value: Any) -> Any:
    return value.isoformat() if hasattr(value, "isoformat") else value


def _pcp_actor(user: Any) -> str:
    """Identificação estável do analista: id → username → preferred_username → email.

    O usuário é um namespace do middleware JWT; nunca aceita autoria do body.
    """
    for attr in ("id", "username", "preferred_username", "email"):
        value = str(getattr(user, attr, "") or "").strip()
        if value:
            return value
    return "pcp"


def _to_pcp_item(row: dict[str, Any]) -> dict[str, Any]:
    """DTO do PCP: contexto completo para a tratativa — sem session token,
    bench_session_id ou internals de persistência."""
    return {
        "id": row.get("id"),
        "branch": row.get("branch"),
        "productionOrder": row.get("production_order"),
        "operationCode": row.get("operation_code"),
        "reportedWorkCenter": row.get("reported_work_center"),
        "feedbackType": row.get("feedback_type"),
        "reasonCode": row.get("reason_code"),
        "note": row.get("note"),
        "status": row.get("status"),
        "operatorCode": row.get("operator_code"),
        "operatorName": row.get("operator_name"),
        "productCode": row.get("product_code"),
        "productDescription": row.get("product_description"),
        "paProductCode": row.get("pa_product_code"),
        "dueDate": _iso(row.get("due_date")),
        "createdAt": _iso(row.get("created_at")),
        "acknowledgedAt": _iso(row.get("acknowledged_at")),
        "acknowledgedBy": row.get("acknowledged_by"),
        "resolvedAt": _iso(row.get("resolved_at")),
        "resolvedBy": row.get("resolved_by"),
        "resolutionNote": row.get("resolution_note"),
    }


class PcpOperatorFeedbackService:
    def __init__(
        self,
        *,
        branch_access: BranchAccessService,
        feedbacks: OperatorFeedbackService,
        notify: Callable[..., None] | None = None,
    ) -> None:
        self._branch_access = branch_access
        self._feedbacks = feedbacks
        self._notify = notify

    def list_inbox(
        self, user: object | None, *, branch: str
    ) -> dict[str, Any]:
        """Feedbacks ativos (open|acknowledged) da filial — toda a filial,
        não só o CT selecionado: o PCP não caça impedimento centro a centro."""
        self._assert_can_view(user, branch)
        rows = self._feedbacks.list_active(branch=branch)
        open_count = sum(
            1
            for row in rows
            if row.get("status") == OperatorFeedbackStatus.OPEN.value
        )
        acknowledged_count = sum(
            1
            for row in rows
            if row.get("status") == OperatorFeedbackStatus.ACKNOWLEDGED.value
        )
        return {
            "items": [_to_pcp_item(row) for row in rows],
            "summary": {
                "total": len(rows),
                "open": open_count,
                "acknowledged": acknowledged_count,
            },
        }

    def acknowledge(
        self, user: object | None, *, feedback_id: str
    ) -> dict[str, Any]:
        row = self._authorized_feedback(user, feedback_id)
        updated = self._feedbacks.acknowledge(
            row["id"], acknowledged_by=_pcp_actor(user)
        )
        self._notify_change(branch=row["branch"], reason="acknowledged", feedback=updated)
        return _to_pcp_item(updated)

    def resolve(
        self,
        user: object | None,
        *,
        feedback_id: str,
        resolution_note: str | None = None,
    ) -> dict[str, Any]:
        note = (resolution_note or "").strip() or None
        if note and len(note) > _RESOLUTION_NOTE_MAX:
            raise ValueError(
                f"Observação da resolução excede {_RESOLUTION_NOTE_MAX} caracteres."
            )
        row = self._authorized_feedback(user, feedback_id)
        updated = self._feedbacks.resolve(
            row["id"], resolved_by=_pcp_actor(user), resolution_note=note
        )
        self._notify_change(branch=row["branch"], reason="resolved", feedback=updated)
        return _to_pcp_item(updated)

    def _assert_can_view(self, user: object | None, branch: str) -> str:
        """Mesma autorização da Carga Máquina: acesso + filial + machine-load.view."""
        self._branch_access.assert_can_view_branch(user, branch)
        if not can(user, PC_MACHINE_LOAD_VIEW):
            raise PermissionError(
                "Você não tem permissão para ver a carga máquina."
            )

    def _authorized_feedback(
        self, user: object | None, feedback_id: str
    ) -> dict[str, Any]:
        """Busca o registro, descobre a filial real e só então autoriza —
        quem não tem acesso à filial não trata o impedimento pelo UUID."""
        row = self._feedbacks.get(str(feedback_id))
        if row is None:
            raise OperatorFeedbackNotFound("Feedback inexistente.")
        self._assert_can_view(user, str(row.get("branch") or ""))
        return row

    def _notify_change(
        self, *, branch: str, reason: str, feedback: dict[str, Any]
    ) -> None:
        """Realtime é best-effort: acknowledge/resolve já persistiram — falha
        no socket nunca transforma o fato em erro para o PCP."""
        if self._notify is None:
            return
        try:
            self._notify(branch=branch, reason=reason, feedback=feedback)
        except Exception:  # noqa: BLE001
            logger.warning(
                "operator_feedback_pcp_notify_failed", exc_info=True
            )
