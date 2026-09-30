"""Resolução do threshold de parada automática (Fase 2 — Parte 2.7).

Regra pura, sem IO: decide quantos segundos sem incremento de peças um run
pode ficar antes da parada automática. O threshold dinâmico usa o ciclo
congelado no Play (ideal_cycle_seconds_snapshot) e só se aplica a
manual_workstation com qualidade de tempo padrão complete.

Fallback é a norma: qualquer entrada ausente/degradada devolve o threshold
legado PC_MES_AUTO_DOWNTIME_SECONDS — nunca reduz o tempo de detecção
por conta própria (o piso minimum_seconds garante isso por default).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from production_control_app.domain.services.production_run_standard_time import (
    COMPLETE,
    MANUAL_WORKSTATION,
)

SOURCE_DISABLED = "disabled"
SOURCE_LEGACY_DYNAMIC_DISABLED = "legacy_dynamic_disabled"
SOURCE_LEGACY_INVALID_CONFIG = "legacy_invalid_config"
SOURCE_LEGACY_UNKNOWN_WORKSTATION = "legacy_unknown_workstation"
SOURCE_LEGACY_STANDARD_TIME_UNAVAILABLE = "legacy_standard_time_unavailable"
SOURCE_LEGACY_INVALID_STANDARD_TIME = "legacy_invalid_standard_time"
SOURCE_DYNAMIC_MANUAL_CYCLE = "dynamic_manual_cycle"


@dataclass(frozen=True)
class AutoDowntimeThreshold:
    """Resultado auditável da resolução — o audit da parada registra a fonte."""

    seconds: int
    source: str
    dynamic: bool
    ideal_cycle_seconds: float | None
    workstation_type: str | None
    cycle_multiplier: float
    minimum_seconds: int


def _float_or_none(value: Any) -> float | None:
    try:
        result = float(value) if value is not None else None
    except (TypeError, ValueError):
        return None
    return result if result is not None and math.isfinite(result) else None


def resolve_auto_downtime_threshold(
    *,
    legacy_seconds: int,
    dynamic_enabled: bool,
    ideal_cycle_seconds: Any,
    standard_time_data_quality: Any,
    workstation_type: Any,
    minimum_seconds: int,
    manual_cycle_multiplier: float,
) -> AutoDowntimeThreshold:
    """Resolve o threshold efetivo em segundos para um run.

    Ordem de decisão (cada saída preserva a rastreabilidade da escolha):

    1. legacy_seconds <= 0 → disabled (kill switch soberano);
    2. flag dinâmica desligada → legacy_dynamic_disabled;
    3. multiplicador/mínimo inválidos → legacy_invalid_config;
    4. posto não manual_workstation → legacy_unknown_workstation;
    5. qualidade do tempo padrão != complete → fallback;
    6. ciclo ausente/inválido → legacy_invalid_standard_time;
    7. ceil(ciclo × multiplicador) com piso → dynamic_manual_cycle.
    """
    legacy = max(int(legacy_seconds or 0), 0)
    cycle = _float_or_none(ideal_cycle_seconds)
    wtype = workstation_type if isinstance(workstation_type, str) else None
    multiplier = _float_or_none(manual_cycle_multiplier) or 0.0
    minimum = (
        int(minimum_seconds)
        if _float_or_none(minimum_seconds) is not None
        else legacy
    )

    def result(
        seconds: int, source: str, *, dynamic: bool = False
    ) -> AutoDowntimeThreshold:
        return AutoDowntimeThreshold(
            seconds=seconds,
            source=source,
            dynamic=dynamic,
            ideal_cycle_seconds=cycle,
            workstation_type=wtype,
            cycle_multiplier=multiplier,
            minimum_seconds=minimum,
        )

    if legacy <= 0:
        return result(0, SOURCE_DISABLED)
    if not dynamic_enabled:
        return result(legacy, SOURCE_LEGACY_DYNAMIC_DISABLED)
    if multiplier <= 0 or minimum < 0:
        return result(legacy, SOURCE_LEGACY_INVALID_CONFIG)
    if wtype != MANUAL_WORKSTATION:
        return result(legacy, SOURCE_LEGACY_UNKNOWN_WORKSTATION)
    if standard_time_data_quality != COMPLETE:
        return result(legacy, SOURCE_LEGACY_STANDARD_TIME_UNAVAILABLE)
    if cycle is None or cycle <= 0:
        return result(legacy, SOURCE_LEGACY_INVALID_STANDARD_TIME)
    candidate = math.ceil(cycle * multiplier)
    return result(max(minimum, candidate), SOURCE_DYNAMIC_MANUAL_CYCLE, dynamic=True)
