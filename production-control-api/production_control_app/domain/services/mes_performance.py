"""Motor puro de Performance MES do Production Run (Fase 2.4).

Performance = tempo teoricamente necessário ÷ tempo efetivamente produzindo:

    ideal_production_seconds = ideal_cycle_seconds x produced_pieces
    performance_percent      = ideal_production_seconds / producing_seconds x 100

Somente o estado producing entra no denominador — stopped, setup,
planned_stop e pausas são dimensões de disponibilidade, não de velocidade.

O calculator é determinístico e isolado: sem banco, sem HTTP, sem TOTVS,
sem Pulse. As entradas já chegam congeladas/persistidas pela aplicação.

Notas de escopo:
- setup_seconds_snapshot NÃO entra na fórmula — o estado MES já separa
  setup de producing; descontar de novo duplicaria a interpretação.
- Performance pode ultrapassar 100% (produção acima do padrão, padrão
  desatualizado etc.): o fato é exposto, nunca truncado em 100.
- Nada aqui é persistido: as métricas são sempre derivadas.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

QUALITY_COMPLETE = "complete"
QUALITY_INSUFFICIENT_COUNT = "insufficient_count_data"
QUALITY_INSUFFICIENT_PRODUCING = "insufficient_producing_time"
QUALITY_INVALID_SNAPSHOT = "invalid_standard_time_snapshot"


def _dec(value: Any) -> Decimal | None:
    """Conversão defensiva para Decimal; None quando inválido/ausente."""
    if value is None:
        return None
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return parsed if parsed.is_finite() else None


def _round6(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.000001")).normalize()


def _round2(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"))


def _num(value: Decimal | None) -> float | None:
    """Boundary: Decimal → float já arredondado (JSON-safe)."""
    return float(value) if value is not None else None


class MesPerformanceCalculator:
    """Calcula métricas derivadas de Performance para um run.

    Entradas: ciclo ideal congelado (s/peça), peças produzidas canônicas
    (production_runs.pieces_total — já líquidas de corrections) e tempo
    em producing derivado da timeline MES. Saída: métricas + qualidade.
    """

    def calculate(
        self,
        *,
        ideal_cycle_seconds: Any,
        produced_pieces: Any,
        producing_seconds: Any,
        standard_time_data_quality: Any,
    ) -> dict[str, Any]:
        cycle = _dec(ideal_cycle_seconds)
        pieces = int(_dec(produced_pieces) or 0)
        pieces = max(0, pieces)
        producing = _dec(producing_seconds) or Decimal("0")
        producing = max(Decimal("0"), producing)

        quality = standard_time_data_quality or "standard_time_unavailable"
        cycle_valid = cycle is not None and cycle > 0

        # Snapshot congelado inválido (ciclo <=0/não numérico) mesmo marcado
        # como complete: degrada a qualidade e zera as métricas dependentes.
        if quality == QUALITY_COMPLETE and not cycle_valid:
            quality = QUALITY_INVALID_SNAPSHOT

        dependent = quality == QUALITY_COMPLETE and cycle_valid
        ideal_production = (cycle * pieces) if cycle_valid else None

        measurable = pieces > 0 and producing > 0
        if dependent and pieces == 0:
            quality = QUALITY_INSUFFICIENT_COUNT
        elif dependent and not measurable:
            quality = QUALITY_INSUFFICIENT_PRODUCING
        elif dependent:
            quality = QUALITY_COMPLETE

        performance = None
        if dependent and measurable and ideal_production is not None:
            performance = _round2(ideal_production / producing * 100)

        return {
            "idealCycleSeconds": _num(_round6(cycle)) if cycle_valid else None,
            "producedPieces": pieces,
            "producingSeconds": float(_round6(producing)),
            "idealProductionSeconds": (
                _num(_round6(ideal_production))
                if ideal_production is not None else None
            ),
            "performancePercent": _num(performance),
            # Ciclo médio AGREGADO do run (producing/peças) — não é ciclo
            # observado por peça nem mediana de intervalos entre eventos.
            "actualAverageCycleSeconds": (
                _num(_round6(producing / pieces)) if measurable else None
            ),
            "actualThroughputPerHour": (
                _num(_round6(Decimal(pieces) * 3600 / producing))
                if measurable else None
            ),
            "expectedThroughputPerHour": (
                _num(_round6(Decimal(3600) / cycle)) if cycle_valid else None
            ),
            "dataQuality": quality,
        }
