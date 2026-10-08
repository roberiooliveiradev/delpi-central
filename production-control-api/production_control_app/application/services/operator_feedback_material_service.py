"""Lifecycle dos materiais do Operator Feedback (C5).

Espelha a semântica da C1: transições condicionais atômicas no repositório,
idempotentes no estado já alcançado (retry não reescreve autoria) e 409 na
transição inválida. Uma regra extra do domínio: material de feedback resolved
não transiciona — impedimento encerrado não pede mais separação.

Nada aqui toca MES, Pulse, downtime ou a Carga Máquina.
"""

from __future__ import annotations

from typing import Any

from production_control_app.domain.errors import (
    OperatorFeedbackMaterialNotFound,
    OperatorFeedbackMaterialStateError,
)
from production_control_app.domain.operator_feedback_material import (
    OperatorFeedbackMaterialStatus,
)
from production_control_app.domain.ports.operator_feedback_material_repository import (  # noqa: E501
    OperatorFeedbackMaterialRepositoryPort,
)

_ACTIVE_FEEDBACK = frozenset({"open", "acknowledged"})


def _require(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"Campo obrigatório ausente: {field}")
    return text


class OperatorFeedbackMaterialService:
    def __init__(
        self, materials: OperatorFeedbackMaterialRepositoryPort
    ) -> None:
        self._materials = materials

    def list_for_feedback(self, feedback_id: str) -> list[dict[str, Any]]:
        return self._materials.list_for_feedbacks([str(feedback_id)]).get(
            str(feedback_id), []
        )

    def list_for_feedbacks(
        self, feedback_ids: list[str]
    ) -> dict[str, list[dict[str, Any]]]:
        return self._materials.list_for_feedbacks(
            [str(item) for item in feedback_ids]
        )

    def mark_picked(
        self, material_id: str, *, picked_by: str
    ) -> dict[str, Any]:
        """pending -> picked. Idempotente sobre já picked."""
        by = _require(picked_by, "picked_by")
        row = self._materials.mark_picked(str(material_id), picked_by=by)
        if row is not None:
            return row
        return self._after_transition(
            material_id,
            idempotent_status=OperatorFeedbackMaterialStatus.PICKED,
        )

    def mark_delivered(
        self, material_id: str, *, delivered_by: str
    ) -> dict[str, Any]:
        """picked -> delivered. Idempotente sobre já delivered."""
        by = _require(delivered_by, "delivered_by")
        row = self._materials.mark_delivered(
            str(material_id), delivered_by=by
        )
        if row is not None:
            return row
        return self._after_transition(
            material_id,
            idempotent_status=OperatorFeedbackMaterialStatus.DELIVERED,
        )

    def _after_transition(
        self,
        material_id: str,
        *,
        idempotent_status: OperatorFeedbackMaterialStatus,
    ) -> dict[str, Any]:
        """UPDATE condicional não casou linha: id inexistente, estado já
        alcançado (idempotente) ou transição inválida — incluindo material
        cujo feedback já foi resolvido pelo PCP."""
        row = self._materials.get_material(str(material_id))
        if row is None:
            raise OperatorFeedbackMaterialNotFound(
                "Material do impedimento não encontrado."
            )
        if str(row.get("feedback_status") or "") not in _ACTIVE_FEEDBACK:
            raise OperatorFeedbackMaterialStateError(
                "Este impedimento já foi resolvido pelo PCP."
            )
        if row.get("status") == idempotent_status.value:
            return row
        raise OperatorFeedbackMaterialStateError(
            f"Transição inválida: material em status {row.get('status')}."
        )
