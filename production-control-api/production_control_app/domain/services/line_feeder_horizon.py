"""Motor puro do horizonte de produção do Alimentador de Linha (Etapa 2).

Percorre a fila PUBLISHED de um CT e aloca um orçamento de horas independente.
Não consulta TOTVS, não reordena e não inventa saldo/tempo.

Política de setup (evidência SH6 + tempo previsto TOTVS):
- ``operation_produced_qty > 0`` → setup já incorrido (não inclui).
- ``operation_produced_qty == 0`` → inclui ``setup_seconds`` uma vez.
- produzido ausente/desconhecido → inclui setup e marca ``setup_uncertain``
  (fail-closed: não afirma que o setup já ocorreu).

Quantidades de saldo (SH6/SC2) estão em unidade operacional (ex.: MI).
``ideal_cycle_seconds`` já é segundos por peça física. Conversão:

``physical_pieces = pending_qty × pieces_conversion_factor``
``remaining_seconds = physical_pieces × ideal_cycle_seconds``

Uma única conversão — nunca ``pending × cycle`` sem o fator quando factor≠1.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN, InvalidOperation
from typing import Any, Sequence

SETUP_WAIVED_PRODUCED = "waived_produced"
SETUP_APPLICABLE = "applicable"
SETUP_UNCERTAIN = "uncertain"
SETUP_NONE = "none"

COVERAGE_FULL = "full"
COVERAGE_PARTIAL = "partial"
COVERAGE_NONE = "none"
COVERAGE_SKIPPED_CLOSED = "skipped_closed"

COMPLETENESS_COMPLETE = "complete"
COMPLETENESS_INCOMPLETE = "incomplete"
COMPLETENESS_SHORTFALL = "shortfall"

_SECONDS_PER_HOUR = Decimal("3600")
_QTY_QUANTUM = Decimal("0.000001")


def _dec(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    if not number.is_finite():
        return None
    return number


def _positive_dec(value: Any) -> Decimal | None:
    number = _dec(value)
    if number is None or number <= 0:
        return None
    return number


def physical_pieces_from_operational(
    pending_qty: Decimal,
    pieces_conversion_factor: Decimal,
) -> Decimal:
    """Converte saldo operacional → peças físicas (única conversão)."""
    return pending_qty * pieces_conversion_factor


def resolve_setup_seconds(
    *,
    setup_seconds: Decimal | None,
    produced_qty: Decimal | None,
) -> tuple[Decimal, str, bool]:
    """(setup_a_aplicar, política, qualidade_incerta).

    Setup é preparação fixa (uma vez). Produção SH6 > 0 comprova início.
    """
    setup = setup_seconds if setup_seconds is not None and setup_seconds >= 0 else Decimal("0")
    if produced_qty is not None and produced_qty > 0:
        return Decimal("0"), SETUP_WAIVED_PRODUCED, False
    if produced_qty is not None and produced_qty == 0:
        return setup, SETUP_APPLICABLE if setup > 0 else SETUP_NONE, False
    # Produzido desconhecido: não afirmar que o setup já ocorreu.
    return setup, SETUP_UNCERTAIN if setup > 0 else SETUP_NONE, True


@dataclass(frozen=True, slots=True)
class HorizonOperationInput:
    operation_id: str
    sequence_position: int
    work_center: str
    work_center_name: str
    production_order: str
    operation_code: str
    product_code: str
    unit: str
    pending_qty: Decimal | None
    produced_qty: Decimal | None
    balance_state: str
    ideal_cycle_seconds: Decimal | None
    setup_seconds: Decimal | None
    pieces_conversion_factor: Decimal | None
    standard_time_quality: str
    standard_time_source: str


@dataclass(frozen=True, slots=True)
class HorizonOperationAllocation:
    operation_id: str
    sequence_position: int
    work_center: str
    work_center_name: str
    production_order: str
    operation_code: str
    product_code: str
    unit: str
    coverage: str
    pending_qty: float | None
    covered_qty: float | None
    remaining_outside_qty: float | None
    pending_physical_pieces: float | None
    covered_physical_pieces: float | None
    setup_seconds_applied: float
    setup_policy: str
    productive_seconds: float
    total_seconds: float
    offset_start_seconds: float
    offset_end_seconds: float
    ideal_cycle_seconds: float | None
    pieces_conversion_factor: float | None
    standard_time_quality: str
    standard_time_source: str
    balance_state: str


@dataclass(frozen=True, slots=True)
class WorkCenterHorizonResult:
    work_center: str
    work_center_name: str
    hours_requested: float
    seconds_budget: float
    seconds_covered: float
    hours_covered: float
    hours_shortfall: float
    completeness: str
    stop_reason: str | None
    setup_uncertain: bool
    operations: tuple[HorizonOperationAllocation, ...]
    skipped_closed_count: int


def allocate_work_center_horizon(
    operations: Sequence[HorizonOperationInput],
    *,
    hours: float | Decimal,
    work_center: str,
    work_center_name: str = "",
) -> WorkCenterHorizonResult:
    """Aloca o orçamento de horas na ordem recebida (já a ordem PUBLISHED)."""
    budget_hours = _positive_dec(hours)
    if budget_hours is None:
        raise ValueError("O horizonte em horas deve ser finito e positivo.")
    budget = budget_hours * _SECONDS_PER_HOUR
    remaining_budget = budget
    elapsed = Decimal("0")
    allocations: list[HorizonOperationAllocation] = []
    skipped_closed = 0
    completeness = COMPLETENESS_COMPLETE
    stop_reason: str | None = None
    setup_uncertain = False

    for item in operations:
        if remaining_budget <= 0:
            completeness = COMPLETENESS_SHORTFALL
            stop_reason = "budget_exhausted"
            break

        if item.balance_state == "closed" or (
            item.pending_qty is not None and item.pending_qty <= 0
        ):
            skipped_closed += 1
            continue

        if item.balance_state == "unknown" or item.pending_qty is None:
            completeness = COMPLETENESS_INCOMPLETE
            stop_reason = "balance_unknown"
            break

        if item.standard_time_quality != "complete":
            completeness = COMPLETENESS_INCOMPLETE
            stop_reason = item.standard_time_quality or "standard_time_unavailable"
            break

        cycle = _positive_dec(item.ideal_cycle_seconds)
        if cycle is None:
            completeness = COMPLETENESS_INCOMPLETE
            stop_reason = "standard_time_unavailable"
            break

        factor = _positive_dec(item.pieces_conversion_factor)
        if factor is None:
            completeness = COMPLETENESS_INCOMPLETE
            stop_reason = "piece_conversion_unavailable"
            break

        pending = item.pending_qty
        assert pending is not None and pending > 0
        remaining_physical = physical_pieces_from_operational(pending, factor)

        setup_applied, setup_policy, uncertain = resolve_setup_seconds(
            setup_seconds=_dec(item.setup_seconds) or Decimal("0"),
            produced_qty=item.produced_qty,
        )
        if uncertain:
            setup_uncertain = True
            # Não apresentar estimativa como exata — CT incompleto, mas
            # ainda aloca com setup incluído (fail-closed conservador).
            completeness = COMPLETENESS_INCOMPLETE
            if stop_reason is None:
                stop_reason = "setup_uncertain"

        if setup_applied > remaining_budget:
            # Setup não cabe inteiro: não inicia operação nem inventa qty.
            completeness = COMPLETENESS_SHORTFALL
            stop_reason = "insufficient_time_for_setup"
            break

        productive_budget = remaining_budget - setup_applied
        if productive_budget <= 0:
            completeness = COMPLETENESS_SHORTFALL
            stop_reason = "no_productive_time_after_setup"
            break

        max_physical = (productive_budget / cycle).to_integral_value(
            rounding=ROUND_DOWN
        )
        # Garante que covered * cycle + setup não ultrapasse o orçamento
        # mesmo com arredondamento decimal residual.
        while max_physical > 0 and setup_applied + max_physical * cycle > remaining_budget:
            max_physical -= 1

        covered_physical = min(remaining_physical, max_physical)
        if covered_physical <= 0:
            completeness = COMPLETENESS_SHORTFALL
            stop_reason = "no_productive_time_after_setup"
            break

        covered_operational = (covered_physical / factor).quantize(
            _QTY_QUANTUM, rounding=ROUND_DOWN
        )
        # Evita covered_qty > pending por artefato de quantize.
        if covered_operational > pending:
            covered_operational = pending
        outside = pending - covered_operational
        if outside < 0:
            outside = Decimal("0")

        productive_seconds = covered_physical * cycle
        total_seconds = setup_applied + productive_seconds
        offset_start = elapsed
        offset_end = elapsed + total_seconds

        if covered_physical + Decimal("1e-12") < remaining_physical:
            coverage = COVERAGE_PARTIAL
        else:
            coverage = COVERAGE_FULL

        allocations.append(
            HorizonOperationAllocation(
                operation_id=item.operation_id,
                sequence_position=item.sequence_position,
                work_center=item.work_center,
                work_center_name=item.work_center_name,
                production_order=item.production_order,
                operation_code=item.operation_code,
                product_code=item.product_code,
                unit=item.unit,
                coverage=coverage,
                pending_qty=float(pending),
                covered_qty=float(covered_operational),
                remaining_outside_qty=float(outside),
                pending_physical_pieces=float(remaining_physical),
                covered_physical_pieces=float(covered_physical),
                setup_seconds_applied=float(setup_applied),
                setup_policy=setup_policy,
                productive_seconds=float(productive_seconds),
                total_seconds=float(total_seconds),
                offset_start_seconds=float(offset_start),
                offset_end_seconds=float(offset_end),
                ideal_cycle_seconds=float(cycle),
                pieces_conversion_factor=float(factor),
                standard_time_quality=item.standard_time_quality,
                standard_time_source=item.standard_time_source,
                balance_state=item.balance_state,
            )
        )

        elapsed += total_seconds
        remaining_budget -= total_seconds

        if coverage == COVERAGE_PARTIAL:
            if remaining_budget > 0 and remaining_budget < cycle:
                # sobra menor que uma peça — shortfall residual transparente
                pass
            break

    seconds_covered = budget - remaining_budget
    if seconds_covered < 0:
        seconds_covered = Decimal("0")
    hours_covered = seconds_covered / _SECONDS_PER_HOUR
    hours_shortfall = remaining_budget / _SECONDS_PER_HOUR

    if completeness == COMPLETENESS_COMPLETE and remaining_budget > 0:
        # Ainda há orçamento mas a fila acabou.
        completeness = COMPLETENESS_SHORTFALL
        stop_reason = stop_reason or "queue_shorter_than_horizon"

    if completeness == COMPLETENESS_COMPLETE and setup_uncertain:
        completeness = COMPLETENESS_INCOMPLETE
        stop_reason = stop_reason or "setup_uncertain"

    return WorkCenterHorizonResult(
        work_center=work_center,
        work_center_name=work_center_name,
        hours_requested=float(budget_hours),
        seconds_budget=float(budget),
        seconds_covered=float(seconds_covered),
        hours_covered=float(hours_covered),
        hours_shortfall=float(hours_shortfall),
        completeness=completeness,
        stop_reason=stop_reason,
        setup_uncertain=setup_uncertain,
        operations=tuple(allocations),
        skipped_closed_count=skipped_closed,
    )


def work_center_result_payload(result: WorkCenterHorizonResult) -> dict[str, Any]:
    return {
        "work_center": result.work_center,
        "work_center_name": result.work_center_name,
        "hours_requested": result.hours_requested,
        "seconds_budget": result.seconds_budget,
        "seconds_covered": result.seconds_covered,
        "hours_covered": result.hours_covered,
        "hours_shortfall": result.hours_shortfall,
        "completeness": result.completeness,
        "stop_reason": result.stop_reason,
        "setup_uncertain": result.setup_uncertain,
        "skipped_closed_count": result.skipped_closed_count,
        "operations": [
            {
                "operation_id": op.operation_id,
                "sequence_position": op.sequence_position,
                "work_center": op.work_center,
                "work_center_name": op.work_center_name,
                "production_order": op.production_order,
                "operation_code": op.operation_code,
                "product_code": op.product_code,
                "unit": op.unit,
                "coverage": op.coverage,
                "pending_qty": op.pending_qty,
                "covered_qty": op.covered_qty,
                "remaining_outside_qty": op.remaining_outside_qty,
                "pending_physical_pieces": op.pending_physical_pieces,
                "covered_physical_pieces": op.covered_physical_pieces,
                "setup_seconds_applied": op.setup_seconds_applied,
                "setup_policy": op.setup_policy,
                "productive_seconds": op.productive_seconds,
                "total_seconds": op.total_seconds,
                "offset_start_seconds": op.offset_start_seconds,
                "offset_end_seconds": op.offset_end_seconds,
                "ideal_cycle_seconds": op.ideal_cycle_seconds,
                "pieces_conversion_factor": op.pieces_conversion_factor,
                "standard_time_quality": op.standard_time_quality,
                "standard_time_source": op.standard_time_source,
                "balance_state": op.balance_state,
            }
            for op in result.operations
        ],
    }
