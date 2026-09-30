"""Tempo padrão canônico de operação de OP (SC2/SHY → fallback SG2).

Única definição conceitual do tempo unitário padrão na api-delpi — a mesma
prioridade usada por ``production_meta_por_hora`` e pelo SQL de eficiência
fabril (``FABRIL_UNIT_HOURS_SQL``):

1. ``SHY.HY_TEMPAD`` — horas padrão por unidade congeladas na OP (snapshot);
2. ``SHY.HY_TEMPOM / SHY.HY_QUANT`` — quando TEMPAD ausente;
3. ``SG2.G2_TEMPAD`` — cadastro atual do roteiro (último recurso);
4. indisponível.

O MES/Pulse conta peças físicas, então ``ideal_cycle_seconds`` é normalizado
por ``pieces_conversion_factor`` da unidade operacional
(``production_operational_units.json``) — ex.: tempo em horas/milheiro (MI)
é dividido por 1000 antes de virar segundos por peça.

``setup_seconds`` é conceito separado (preparação fixa) e nunca entra no
ciclo unitário.
"""

from __future__ import annotations

from dataclasses import dataclass

STANDARD_TIME_SOURCE_SHY_TEMPAD = "shy_tempad"
STANDARD_TIME_SOURCE_SHY_TEMPOM_QUANT = "shy_tempom_quant"
STANDARD_TIME_SOURCE_SG2_TEMPAD = "sg2_tempad"
STANDARD_TIME_SOURCE_UNAVAILABLE = "unavailable"

STANDARD_TIME_SOURCES = frozenset(
    {
        STANDARD_TIME_SOURCE_SHY_TEMPAD,
        STANDARD_TIME_SOURCE_SHY_TEMPOM_QUANT,
        STANDARD_TIME_SOURCE_SG2_TEMPAD,
        STANDARD_TIME_SOURCE_UNAVAILABLE,
    }
)

DATA_QUALITY_COMPLETE = "complete"
DATA_QUALITY_STANDARD_TIME_UNAVAILABLE = "standard_time_unavailable"
DATA_QUALITY_PIECE_CONVERSION_UNAVAILABLE = "piece_conversion_unavailable"

_DECIMAL_PLACES = 6
_SECONDS_PER_HOUR = 3600.0


@dataclass(frozen=True, slots=True)
class OperationStandardTime:
    standard_time_unit_hours: float | None
    ideal_cycle_seconds: float | None
    setup_seconds: float
    pieces_conversion_factor: float | None
    standard_time_source: str
    data_quality: str


def resolve_standard_time_unit_hours(
    *,
    hy_tempad: float | int | None = None,
    hy_tempom: float | int | None = None,
    hy_quant: float | int | None = None,
    g2_tempad: float | int | None = None,
) -> tuple[float | None, str]:
    """Horas por unidade operacional + origem, na prioridade canônica.

    Mesma cadeia do SQL ``FABRIL_UNIT_HOURS_SQL`` — mudança aqui vale para
    meta/hora, tempo previsto e a leitura MES.
    """
    tempad = _positive_float(hy_tempad)
    if tempad is not None:
        return tempad, STANDARD_TIME_SOURCE_SHY_TEMPAD

    tempom = _positive_float(hy_tempom)
    quant = _positive_float(hy_quant)
    if tempom is not None and quant is not None:
        return tempom / quant, STANDARD_TIME_SOURCE_SHY_TEMPOM_QUANT

    g2 = _positive_float(g2_tempad)
    if g2 is not None:
        return g2, STANDARD_TIME_SOURCE_SG2_TEMPAD

    return None, STANDARD_TIME_SOURCE_UNAVAILABLE


def resolve_setup_hours(
    *,
    hy_setup: float | int | None = None,
    g2_setup: float | int | None = None,
) -> float:
    """Setup em horas: ``COALESCE(SHY.HY_SETUP, SG2.G2_SETUP, 0)`` canônico."""
    setup = _nullable_float(hy_setup)
    if setup is None:
        setup = _nullable_float(g2_setup)
    return setup if setup is not None else 0.0


def compute_operation_standard_time(
    *,
    hy_tempad: float | int | None = None,
    hy_tempom: float | int | None = None,
    hy_quant: float | int | None = None,
    g2_tempad: float | int | None = None,
    hy_setup: float | int | None = None,
    g2_setup: float | int | None = None,
    pieces_conversion_factor: float | int | None = None,
) -> OperationStandardTime:
    """Normaliza o tempo padrão para segundos por peça física.

    ``ideal_cycle_seconds = unit_hours × 3600 ÷ pieces_conversion_factor``
    somente quando ambos são positivos. Unidade sem fator (ex.: MT) devolve
    ``ideal_cycle_seconds = None`` com ``piece_conversion_unavailable`` —
    nunca um número inventado.
    """
    unit_hours, source = resolve_standard_time_unit_hours(
        hy_tempad=hy_tempad,
        hy_tempom=hy_tempom,
        hy_quant=hy_quant,
        g2_tempad=g2_tempad,
    )
    setup_seconds = round(
        resolve_setup_hours(hy_setup=hy_setup, g2_setup=g2_setup)
        * _SECONDS_PER_HOUR,
        _DECIMAL_PLACES,
    )
    factor = _positive_float(pieces_conversion_factor)

    if unit_hours is None:
        return OperationStandardTime(
            standard_time_unit_hours=None,
            ideal_cycle_seconds=None,
            setup_seconds=setup_seconds,
            pieces_conversion_factor=factor,
            standard_time_source=source,
            data_quality=DATA_QUALITY_STANDARD_TIME_UNAVAILABLE,
        )

    rounded_unit_hours = round(unit_hours, _DECIMAL_PLACES)
    if factor is None:
        return OperationStandardTime(
            standard_time_unit_hours=rounded_unit_hours,
            ideal_cycle_seconds=None,
            setup_seconds=setup_seconds,
            pieces_conversion_factor=None,
            standard_time_source=source,
            data_quality=DATA_QUALITY_PIECE_CONVERSION_UNAVAILABLE,
        )

    return OperationStandardTime(
        standard_time_unit_hours=rounded_unit_hours,
        ideal_cycle_seconds=round(
            unit_hours * _SECONDS_PER_HOUR / factor, _DECIMAL_PLACES
        ),
        setup_seconds=setup_seconds,
        pieces_conversion_factor=factor,
        standard_time_source=source,
        data_quality=DATA_QUALITY_COMPLETE,
    )


def _positive_float(value: float | int | None) -> float | None:
    number = _nullable_float(value)
    if number is None or number <= 0:
        return None
    return number


def _nullable_float(value: float | int | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
