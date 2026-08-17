"""Turnos de fábrica Delpi — classificação por horário de início do apontamento.

Espelha a regra canônica do plugin eficiência-fabril (`constants/shifts.ts`).
Não depende de locale do SO.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Optional

FACTORY_SHIFT_IDS: tuple[str, ...] = ("1", "2", "3")


@dataclass(frozen=True, slots=True)
class FactoryShiftDefinition:
    id: str
    label: str
    start: str
    end: str
    start_minutes: int
    end_minutes: int


FACTORY_SHIFTS: tuple[FactoryShiftDefinition, ...] = (
    FactoryShiftDefinition(
        id="1",
        label="1º Turno",
        start="04:34",
        end="14:17",
        start_minutes=4 * 60 + 34,
        end_minutes=14 * 60 + 17,
    ),
    FactoryShiftDefinition(
        id="2",
        label="2º Turno",
        start="14:18",
        end="23:49",
        start_minutes=14 * 60 + 18,
        end_minutes=23 * 60 + 49,
    ),
    FactoryShiftDefinition(
        id="3",
        label="3º Turno",
        start="23:50",
        end="04:33",
        start_minutes=23 * 60 + 50,
        end_minutes=4 * 60 + 33,
    ),
)

_SHIFT_BY_ID = {shift.id: shift for shift in FACTORY_SHIFTS}


def parse_start_time_to_minutes(hora_inicio: str | None) -> int | None:
    """Converte HH:MM / HH:MM:SS (ou com prefixo data ISO) em minutos desde meia-noite."""
    if not hora_inicio:
        return None
    text = str(hora_inicio).strip()
    if not text:
        return None

    # Aceita "04:34", "04:34:00", "2026-01-01T04:34:00"
    match = re.search(r"(?:T|^|\s)(\d{1,2}):(\d{2})(?::(\d{2}))?", text)
    if not match:
        return None
    hours = int(match.group(1))
    minutes = int(match.group(2))
    if hours < 0 or hours > 23 or minutes < 0 or minutes > 59:
        return None
    return hours * 60 + minutes


def _is_within_shift_minutes(minutes: int, start: int, end: int) -> bool:
    if start <= end:
        return start <= minutes <= end
    return minutes >= start or minutes <= end


def resolve_factory_shift(hora_inicio: str | None) -> FactoryShiftDefinition | None:
    """Classifica o turno pelo horário de início do apontamento."""
    minutes = parse_start_time_to_minutes(hora_inicio)
    if minutes is None:
        return None
    for shift in FACTORY_SHIFTS:
        if _is_within_shift_minutes(minutes, shift.start_minutes, shift.end_minutes):
            return shift
    return None


def factory_shift_id(hora_inicio: str | None) -> str | None:
    shift = resolve_factory_shift(hora_inicio)
    return shift.id if shift else None


def factory_shift_label(hora_inicio: str | None) -> str | None:
    shift = resolve_factory_shift(hora_inicio)
    return shift.label if shift else None


def parse_factory_shift_filter(raw: str | None | Iterable[str]) -> tuple[str, ...]:
    """Normaliza query `shift` (único, lista ou CSV) para ids válidos."""
    if raw is None:
        return ()
    if isinstance(raw, str):
        parts = [part.strip() for part in raw.split(",")]
    else:
        parts = []
        for item in raw:
            if item is None:
                continue
            parts.extend(str(part).strip() for part in str(item).split(","))

    selected: list[str] = []
    seen: set[str] = set()
    for part in parts:
        if not part or part in seen:
            continue
        if part not in _SHIFT_BY_ID:
            raise ValueError(
                f"shift inválido: {part!r}. Valores aceitos: {', '.join(FACTORY_SHIFT_IDS)}."
            )
        seen.add(part)
        selected.append(part)
    return tuple(selected)


def matches_factory_shift_filter(
    hora_inicio: str | None,
    *,
    shifts: Optional[Iterable[str]] = None,
    turno: str | None = None,
) -> bool:
    """True se não há filtro ou se o turno do apontamento está na lista."""
    selected = tuple(shifts or ())
    if not selected:
        return True
    item_shift = turno if turno in _SHIFT_BY_ID else factory_shift_id(hora_inicio)
    if item_shift is None:
        return False
    return item_shift in selected
