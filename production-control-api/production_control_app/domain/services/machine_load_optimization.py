"""Motor de sequenciamento composto da carga máquina (O1).

Hierarquia obrigatória da fila de cada centro de trabalho:

1. operação já iniciada → permanece travada no slot atual;
2. data de entrega → menor data primeiro (due_date → pa_due_date);
3. dentro da mesma data, com group_by_tool ativo → grupos pela mesma
   ferramenta, na ordem da **primeira ocorrência livre** da fila — nunca
   ordenação alfabética do código;
4. dentro do mesmo grupo → ordem atual da fila (estável — o ajuste manual
   do PCP continua valendo);
5. MOD/vazio/None → grupo **sem ferramenta**, depois das ferramentas
   reais daquela data, preservando a ordem interna;
6. operação sem data → final da fila, na ordem atual, **sem** reagrupamento
   por ferramenta — o sistema não conhece a urgência delas.

Ferramenta é critério secundário: nunca faz uma data posterior ultrapassar
uma anterior. Novos critérios (ex.: materiais) devem entrar como camadas
adicionais de _desired_free_order, sempre depois da data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from production_control_app.domain.services.machine_load_delivery_window import (
    missing_due_date_count,
    operation_due_date,
)
from production_control_app.domain.services.machine_load_queue_slots import (
    OperationKey,
    free_positions,
    pinned_positions,
    reorder_free_slots,
    slots_by_work_center,
    started_predicate,
)

# «MOD» é mão de obra — operação manual sem ferramental. Espelha o contrato
# MANUAL_LABOR_TOOL_CODE exposto pela api-delpi; o domínio não importa código
# de outro bounded context.
MANUAL_LABOR_TOOL_CODE = "MOD"


@dataclass(frozen=True)
class MachineLoadOptimizationCriteria:
    """Critérios opcionais aplicados **depois** da data de entrega.

    A data é obrigatória nesta iniciativa e por isso não é um flag.
    """

    group_by_tool: bool = False


@dataclass(frozen=True)
class MachineLoadOptimizationResult:
    operations: list[dict[str, Any]]
    #: Só os centros cuja ordem realmente mudou.
    work_centers: list[str]
    moved_operation_count: int
    kept_ahead_count: int
    missing_due_date_count: int


def normalize_tool_group(tool: Any) -> str | None:
    """Grupo de ferramental da operação; None = sem ferramenta.

    Normalização case-insensitive e tolerante a espaços — o valor original
    do item nunca é alterado.
    """
    code = str(tool or "").strip().upper()
    if not code or code == MANUAL_LABOR_TOOL_CODE:
        return None
    return code


def optimize_machine_load_queue(
    operations: list[dict[str, Any]],
    *,
    criteria: MachineLoadOptimizationCriteria,
    started_keys: set[OperationKey] | None = None,
) -> MachineLoadOptimizationResult:
    """Resequencia a fila de cada centro pela hierarquia data → critérios.

    started_keys traz o status ao vivo (HZA) por (production_order,
    operation_code) quando o snapshot congelado não carrega os campos de
    apontamento.
    """
    started_here = started_predicate(started_keys)

    next_ops = list(operations)
    centers: list[str] = []
    moved_count = 0
    kept_ahead = 0

    for center, slots in slots_by_work_center(operations).items():
        center_ops = [operations[index] for index in slots]
        pinned = pinned_positions(center_ops, is_pinned=started_here)
        free = free_positions(center_ops, pinned=pinned)
        if not free:
            continue

        desired = _desired_free_order(center_ops, free, criteria)
        if desired == free:
            continue

        reordered = reorder_free_slots(
            center_ops,
            pinned=pinned,
            desired_free_order=desired,
        )
        for slot, item in zip(slots, reordered, strict=True):
            next_ops[slot] = item

        centers.append(center)
        moved_count += sum(
            1 for before, after in zip(free, desired, strict=True) if before != after
        )
        # Tudo antes da primeira posição livre é operação já iniciada.
        kept_ahead += free[0]

    return MachineLoadOptimizationResult(
        operations=next_ops,
        work_centers=centers,
        moved_operation_count=moved_count,
        kept_ahead_count=kept_ahead,
        missing_due_date_count=missing_due_date_count(operations),
    )


def _desired_free_order(
    center_ops: list[dict[str, Any]],
    free: list[int],
    criteria: MachineLoadOptimizationCriteria,
) -> list[int]:
    """Permutação das posições livres: data → ferramenta → ordem atual.

    O ranking dos grupos de ferramenta é calculado por (centro, data) olhando
    **só os slots livres** — uma ferramenta de operação travada não comanda a
    preferência das livres.
    """
    tool_ranks = _tool_group_ranks(center_ops, free) if criteria.group_by_tool else {}

    def sort_key(position: int) -> tuple[int, str, int]:
        operation = center_ops[position]
        due = operation_due_date(operation)
        # Sem entrega vai para o fim; sorted() é estável, então o empate —
        # inclusive o bloco inteiro sem data — preserva a ordem atual.
        if due is None:
            return (1, "", 0)
        if not criteria.group_by_tool:
            return (0, due, 0)
        tool = normalize_tool_group(operation.get("tool"))
        ranks = tool_ranks.get(due, {})
        # Sem ferramenta fica depois de todos os grupos reais daquela data.
        rank = len(ranks) if tool is None else ranks[tool]
        return (0, due, rank)

    return sorted(free, key=sort_key)


def _tool_group_ranks(
    center_ops: list[dict[str, Any]],
    free: list[int],
) -> dict[str, dict[str, int]]:
    """Ranking de ferramentas por data, na ordem da primeira ocorrência livre."""
    ranks: dict[str, dict[str, int]] = {}
    for position in free:
        due = operation_due_date(center_ops[position])
        if due is None:
            continue
        tool = normalize_tool_group(center_ops[position].get("tool"))
        if tool is None:
            continue
        per_date = ranks.setdefault(due, {})
        if tool not in per_date:
            per_date[tool] = len(per_date)
    return ranks
