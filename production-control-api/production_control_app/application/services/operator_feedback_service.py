"""Serviço de aplicação do Operator Feedback (C1 — fundação).

Orquestra criação e transições do lifecycle open -> acknowledged -> resolved
somente através do port de persistência: sem HTTP, sem WebSocket, sem UI e sem
qualquer leitura do snapshot da Carga Máquina — o contexto da OP chega pronto
do chamador (a C2 validará sessão/OP no cockpit).

Decisões de lifecycle documentadas:
  * acknowledge é IDEMPOTENTE: repetir sobre um já acknowledged devolve o
    registro sem reescrever autoria/horário — retry de rede não destrói prova.
  * resolve também é IDEMPOTENTE sobre já resolved, pelo mesmo motivo.
  * resolved é TERMINAL: nenhuma transição sai dele nesta fase.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from production_control_app.domain.errors import (
    InvalidOperatorFeedbackReason,
    InvalidOperatorFeedbackType,
    OperatorFeedbackNotFound,
    OperatorFeedbackStateError,
)
from production_control_app.domain.operator_feedback import (
    OperatorFeedbackReason,
    OperatorFeedbackStatus,
    OperatorFeedbackType,
)
from production_control_app.domain.ports.operator_feedback_repository import (
    OperatorFeedbackRepositoryPort,
)


def _require(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"Campo obrigatório do feedback ausente: {field}")
    return text


class OperatorFeedbackService:
    def __init__(self, feedbacks: OperatorFeedbackRepositoryPort) -> None:
        self._feedbacks = feedbacks

    def report(
        self,
        *,
        feedback_type: str,
        reason_code: str,
        branch: str,
        production_order: str,
        operation_code: str,
        reported_work_center: str,
        operator_code: str,
        operator_name: str,
        note: str | None = None,
        bench_session_id: str | None = None,
        run_id: str | None = None,
        product_code: str | None = None,
        product_description: str | None = None,
        pa_product_code: str | None = None,
        due_date: date | str | None = None,
    ) -> dict[str, Any]:
        """Registra impedimento em status open; duplicado ativo e rejeitado no banco."""
        type_value = self._validate_type(feedback_type)
        reason_value = self._validate_reason(reason_code)
        return self._feedbacks.create(
            branch=_require(branch, "branch"),
            production_order=_require(production_order, "production_order"),
            operation_code=_require(operation_code, "operation_code"),
            reported_work_center=_require(
                reported_work_center, "reported_work_center"
            ),
            feedback_type=type_value,
            reason_code=reason_value,
            operator_code=_require(operator_code, "operator_code"),
            operator_name=_require(operator_name, "operator_name"),
            note=(note or "").strip() or None,
            bench_session_id=bench_session_id,
            run_id=run_id,
            product_code=product_code,
            product_description=product_description,
            pa_product_code=pa_product_code,
            due_date=due_date,
        )

    def get(self, feedback_id: str) -> dict[str, Any]:
        row = self._feedbacks.get(str(feedback_id))
        if row is None:
            raise OperatorFeedbackNotFound("Feedback inexistente.")
        return row

    def list_active(
        self, *, branch: str, reported_work_center: str | None = None
    ) -> list[dict[str, Any]]:
        return self._feedbacks.list_active(
            branch=_require(branch, "branch"),
            reported_work_center=reported_work_center,
        )

    def list_active_for_operation(
        self,
        *,
        branch: str,
        production_order: str,
        operation_code: str,
    ) -> list[dict[str, Any]]:
        return self._feedbacks.list_active_for_operation(
            branch=_require(branch, "branch"),
            production_order=_require(production_order, "production_order"),
            operation_code=_require(operation_code, "operation_code"),
        )

    def acknowledge(
        self, feedback_id: str, *, acknowledged_by: str
    ) -> dict[str, Any]:
        """open -> acknowledged. Idempotente sobre já acknowledged."""
        by = _require(acknowledged_by, "acknowledged_by")
        row = self._feedbacks.acknowledge(str(feedback_id), acknowledged_by=by)
        if row is not None:
            return row
        return self._after_transition(
            feedback_id,
            idempotent_status=OperatorFeedbackStatus.ACKNOWLEDGED,
        )

    def resolve(
        self,
        feedback_id: str,
        *,
        resolved_by: str,
        resolution_note: str | None = None,
    ) -> dict[str, Any]:
        """open|acknowledged -> resolved. Idempotente sobre já resolved."""
        by = _require(resolved_by, "resolved_by")
        row = self._feedbacks.resolve(
            str(feedback_id),
            resolved_by=by,
            resolution_note=(resolution_note or "").strip() or None,
        )
        if row is not None:
            return row
        return self._after_transition(
            feedback_id,
            idempotent_status=OperatorFeedbackStatus.RESOLVED,
        )

    def _after_transition(
        self,
        feedback_id: str,
        *,
        idempotent_status: OperatorFeedbackStatus,
    ) -> dict[str, Any]:
        """Disambigua o UPDATE condicional que não casou linha.

        Nada transitou porque: id inexistente, estado já alcançado (idempotente)
        ou estado terminal inválido. A distinção vem da leitura atual.
        """
        row = self._feedbacks.get(str(feedback_id))
        if row is None:
            raise OperatorFeedbackNotFound("Feedback inexistente.")
        if row.get("status") == idempotent_status.value:
            return row
        raise OperatorFeedbackStateError(
            f"Transição inválida: feedback em status {row.get('status')}."
        )

    @staticmethod
    def _validate_type(value: str) -> str:
        try:
            return OperatorFeedbackType(str(value or "").strip()).value
        except ValueError as exc:
            raise InvalidOperatorFeedbackType(
                f"Tipo de feedback não suportado: {value}."
            ) from exc

    @staticmethod
    def _validate_reason(value: str) -> str:
        try:
            return OperatorFeedbackReason(str(value or "").strip()).value
        except ValueError as exc:
            raise InvalidOperatorFeedbackReason(
                f"Motivo de feedback não suportado: {value}."
            ) from exc
