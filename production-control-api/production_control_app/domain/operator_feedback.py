"""Operator Feedback — impedimentos comunicados pelo operador ao PCP.

Conceito independente do MES: um feedback diz "não consigo produzir esta OP",
não "a máquina parou". Não altera estado de execução, não é downtime, não usa
motivos de parada e não depende de production_run nem do snapshot da Carga
Máquina (o contexto é congelado no registro).

Catálogo extensível por enum: novos tipos/motivos entram aqui e na camada de
apresentação — a persistência trata tudo como texto governado pelo domínio.
"""

from __future__ import annotations

from enum import StrEnum


class OperatorFeedbackType(StrEnum):
    """O que o operador está comunicando (C1: apenas impedimento de produção)."""

    CANNOT_PRODUCE = "cannot_produce"


class OperatorFeedbackReason(StrEnum):
    """Motivo estruturado do impedimento (C1: apenas falta de material)."""

    MISSING_MATERIAL = "missing_material"


class OperatorFeedbackStatus(StrEnum):
    """Lifecycle: open -> acknowledged -> resolved (resolved é terminal)."""

    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


#: Status que caracterizam impedimento ATIVO — mesma regra do índice parcial
#: uq_pc_operator_feedbacks_active (nunca duplicar impedimento ativo igual).
ACTIVE_STATUSES = frozenset(
    {OperatorFeedbackStatus.OPEN, OperatorFeedbackStatus.ACKNOWLEDGED}
)
