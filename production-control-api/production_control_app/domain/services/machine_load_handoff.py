"""Resolução da próxima operação elegível na troca guiada de OP (handoff).

Regras canônicas, função pura — o chamador já aplicou transferências e
filtrou retiradas na ordem publicada pelo PCP:

- a fila do handoff é o mesmo centro de trabalho (identidade normalizada);
- a operação do run atual precisa estar nessa fila — saiu da fila = bloqueio;
- varredura a partir da posição seguinte à atual:
    * saldo conhecido <= 0 → operação encerrada no planejamento, ignorada;
    * saldo desconhecido → não autoriza a troca automática (fail closed);
    * saldo conhecido > 0 → primeira elegível = alvo da troca;
- fim da fila sem elegível → resultado no_next_operation.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from production_control_app.domain.services.machine_load_transfer import (
    normalize_work_center,
    operation_identity,
)
from production_control_app.domain.services.production_order_key import (
    normalize_order_code,
)


def _optional_float(value: Any) -> float | None:
    try:
        normalized = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    if not normalized.is_finite():
        return None
    return float(normalized)


def operation_balance_state(item: dict[str, Any]) -> str:
    """open | closed | unknown — mesma fonte do saldo da fila.

    operation_pending_qty (saldo da operação) tem precedência; sem ela,
    pending_qty (cabeçalho) — espelho de _has_open_operation_balance,
    mas separando «desconhecido» de «aberto»: na troca guiada, desconhecido
    NÃO autoriza — falha de enriquecimento não pode mover produção sozinha.
    """
    pending = _optional_float(item.get("operation_pending_qty"))
    if pending is None:
        pending = _optional_float(item.get("pending_qty"))
    if pending is None:
        return "unknown"
    return "open" if pending > 1e-9 else "closed"


@dataclass(frozen=True)
class HandoffNextResolution:
    """Resultado determinístico da procura pela próxima elegível."""

    status: str
    """ok | current_not_in_queue | no_next_operation | balance_unknown."""
    target: dict[str, Any] | None = None
    queue_size: int = 0
    current_position: int = 0
    target_position: int = 0
    balance_state: str | None = None
    """Estado de saldo do alvo encontrado (open) ou do bloqueio (unknown)."""

    @property
    def available(self) -> bool:
        return self.status == "ok"


def resolve_handoff_next(
    operations: list[dict[str, Any]],
    *,
    work_center: str,
    production_order: str,
    operation_code: str,
) -> HandoffNextResolution:
    """Primeira operação elegível do mesmo CT após a operação atual.

    operations é a fila publicada inteira (transfers aplicadas, retiradas
    já removidas) na ordem vigente do PCP. A busca nunca cruza centro de
    trabalho nem devolve operação de outra filial — o payload já é da filial.
    """
    center = normalize_work_center(work_center)
    wanted = (
        normalize_order_code(production_order),
        normalize_order_code(operation_code),
    )
    queue = [
        item
        for item in operations
        if normalize_work_center(item.get("work_center")) == center
    ]
    current_index = next(
        (
            index
            for index, item in enumerate(queue)
            if operation_identity(item) == wanted
        ),
        None,
    )
    if current_index is None:
        return HandoffNextResolution(
            status="current_not_in_queue", queue_size=len(queue)
        )
    for index in range(current_index + 1, len(queue)):
        item = queue[index]
        state = operation_balance_state(item)
        if state == "closed":
            continue
        if state == "unknown":
            return HandoffNextResolution(
                status="balance_unknown",
                target=item,
                queue_size=len(queue),
                current_position=current_index + 1,
                target_position=index + 1,
                balance_state="unknown",
            )
        return HandoffNextResolution(
            status="ok",
            target=item,
            queue_size=len(queue),
            current_position=current_index + 1,
            target_position=index + 1,
            balance_state="open",
        )
    return HandoffNextResolution(
        status="no_next_operation",
        queue_size=len(queue),
        current_position=current_index + 1,
    )
