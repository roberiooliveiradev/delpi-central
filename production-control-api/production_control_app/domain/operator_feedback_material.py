"""Materiais estruturados do Operator Feedback (C5).

Quando o impedimento é missing_material, o operador escolhe materiais reais
da OP (SD4); o backend valida e congela o snapshot. Cada material tem
lifecycle operacional próprio — pending -> picked -> delivered — tocado pelo
Alimentador de Linha e INDEPENDENTE do lifecycle do feedback:
material delivered não resolve o impedimento; só o PCP resolve.
"""

from __future__ import annotations

from enum import StrEnum


class OperatorFeedbackMaterialStatus(StrEnum):
    """Workflow da solicitação urgente: pending -> picked -> delivered."""

    PENDING = "pending"
    PICKED = "picked"
    DELIVERED = "delivered"


#: Status que mantêm o material na fila ativa do Alimentador.
ACTIVE_MATERIAL_STATUSES = frozenset(
    {
        OperatorFeedbackMaterialStatus.PENDING,
        OperatorFeedbackMaterialStatus.PICKED,
    }
)

#: Transições permitidas — sem retorno nesta fase.
MATERIAL_TRANSITIONS: dict[OperatorFeedbackMaterialStatus, OperatorFeedbackMaterialStatus] = {
    OperatorFeedbackMaterialStatus.PENDING: OperatorFeedbackMaterialStatus.PICKED,
    OperatorFeedbackMaterialStatus.PICKED: OperatorFeedbackMaterialStatus.DELIVERED,
}
