"""Motor de sequenciamento composto da carga máquina (O1).

Hierarquia obrigatória da fila de cada centro de trabalho:

1. operação com run aberto no cockpit → permanece travada no slot atual;
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

from production_control_app.domain.sequencing_profile import (
    CRITERION_MATERIAL_CODE,
    CRITERION_TOOL_GROUP,
)
from production_control_app.domain.services.line_feeder_requirements import (
    _normalize_operation_code,
)
from production_control_app.domain.services.machine_load_delivery_window import (
    missing_due_date_count,
    operation_due_date,
)
from production_control_app.domain.services.machine_load_queue_slots import (
    ProtectedOperationKey,
    free_positions,
    pinned_positions,
    protected_predicate,
    reorder_free_slots,
    slots_by_work_center,
)
from production_control_app.domain.services.production_order_key import (
    normalize_order_code,
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
class MachineLoadCenterCriteria:
    """Critérios efetivos de um CT, na ordem de precedência após a entrega.

    ``grouping`` usa os tipos de critério do perfil (``tool_group``,
    ``material_code``) já na ordem cadastrada. ``pa_due_date`` nunca aparece
    aqui — é sempre o critério soberano aplicado antes dos grupos.
    """

    grouping: tuple[str, ...] = ()


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
    protected_keys: set[ProtectedOperationKey] | None = None,
    center_criteria: dict[str, MachineLoadCenterCriteria] | None = None,
    material_codes: dict[tuple[str, str, str], str] | None = None,
) -> MachineLoadOptimizationResult:
    """Resequencia a fila de cada centro pela hierarquia data → critérios.

    ``protected_keys`` traz as operações com run aberto no cockpit por
    (work_center, production_order, operation_code) — a única fonte que
    trava posição; flags do snapshot congelado não protegem.

    ``center_criteria`` prevalece sobre ``criteria`` por centro: quando o CT
    tem perfil ativo, os agrupamentos seguem a ordem cadastrada nele (a data
    continua soberana antes de todos). ``material_codes`` traz o código de
    cabo resolvido por (work_center, production_order, operation_code)
    normalizados — operação sem código resolvido não forma grupo artificial.
    """
    is_protected = protected_predicate(protected_keys)
    center_criteria = center_criteria or {}

    next_ops = list(operations)
    centers: list[str] = []
    moved_count = 0
    kept_ahead = 0

    for center, slots in slots_by_work_center(operations).items():
        center_ops = [operations[index] for index in slots]
        pinned = pinned_positions(center_ops, is_pinned=is_protected)
        free = free_positions(center_ops, pinned=pinned)
        if not free:
            continue

        plan = center_criteria.get(center)
        grouping = (
            plan.grouping
            if plan is not None
            else ((CRITERION_TOOL_GROUP,) if criteria.group_by_tool else ())
        )
        desired = _desired_free_order(
            center_ops,
            free,
            grouping=grouping,
            material_codes=material_codes,
            center=center,
        )
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
        # Tudo antes da primeira posição livre é operação com run aberto.
        kept_ahead += free[0]

    return MachineLoadOptimizationResult(
        operations=next_ops,
        work_centers=centers,
        moved_operation_count=moved_count,
        kept_ahead_count=kept_ahead,
        missing_due_date_count=missing_due_date_count(operations),
    )


def _material_identity(
    center: str, operation: dict[str, Any]
) -> tuple[str, str, str]:
    """Chave do material resolvido: (CT atual, OP, operação) normalizados."""
    return (
        center,
        normalize_order_code(operation.get("production_order")),
        _normalize_operation_code(operation.get("operation_code")),
    )


def _group_key_fn(
    name: str,
    center: str,
    material_codes: dict[tuple[str, str, str], str] | None,
) -> Any:
    """Função item → chave de grupo (``None`` = sem grupo, vai por último)."""
    if name == CRITERION_TOOL_GROUP:
        return lambda op: normalize_tool_group(op.get("tool"))
    if name == CRITERION_MATERIAL_CODE:
        codes = material_codes or {}
        return lambda op: codes.get(_material_identity(center, op))
    # Critério não suportado pelo motor nunca é ignorado em silêncio.
    raise ValueError(f"Critério de agrupamento não suportado pelo motor: {name}.")


def _desired_free_order(
    center_ops: list[dict[str, Any]],
    free: list[int],
    *,
    grouping: tuple[str, ...],
    material_codes: dict[tuple[str, str, str], str] | None,
    center: str,
) -> list[int]:
    """Permutação das posições livres: data → grupos cadastrados → ordem atual.

    O ranking de cada critério de agrupamento é calculado por (centro, data)
    olhando **só os slots livres** — um grupo de operação travada não comanda
    a preferência das livres. A ordem dos critérios no perfil vira a ordem
    lexicográfica dos ranks.
    """
    key_fns = [
        _group_key_fn(name, center, material_codes) for name in grouping
    ]
    rankers = [
        _group_ranks(center_ops, free, key_fn=key_fn) for key_fn in key_fns
    ]

    def sort_key(position: int) -> tuple:
        operation = center_ops[position]
        due = operation_due_date(operation)
        # Sem entrega vai para o fim; sorted() é estável, então o empate —
        # inclusive o bloco inteiro sem data — preserva a ordem atual.
        if due is None:
            return (1, "") + (0,) * len(grouping)
        ranks = tuple(
            _group_rank(rankers[index], due, key_fns[index](operation))
            for index in range(len(grouping))
        )
        return (0, due, *ranks)

    return sorted(free, key=sort_key)


def _group_rank(
    ranks: dict[str, dict[str, int]], due: str, key: str | None
) -> int:
    """Posição do grupo na data; sem grupo fica depois de todos os reais."""
    per_date = ranks.get(due, {})
    if key is not None and key in per_date:
        return per_date[key]
    return len(per_date)


def _group_ranks(
    center_ops: list[dict[str, Any]],
    free: list[int],
    *,
    key_fn: Any,
) -> dict[str, dict[str, int]]:
    """Ranking de grupos por data, na ordem da primeira ocorrência livre."""
    ranks: dict[str, dict[str, int]] = {}
    for position in free:
        due = operation_due_date(center_ops[position])
        if due is None:
            continue
        key = key_fn(center_ops[position])
        if key is None:
            continue
        per_date = ranks.setdefault(due, {})
        if key not in per_date:
            per_date[key] = len(per_date)
    return ranks
