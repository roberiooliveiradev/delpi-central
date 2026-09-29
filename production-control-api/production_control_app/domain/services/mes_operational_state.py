"""Domínio MES — estado operacional do CT e paradas (fundação).

Três conceitos que não podem se confundir:

- ciclo de vida do run: running | paused | completed | aborted
- estado operacional do CT: idle | setup | producing | stopped | planned_stop
- saúde da telemetria Pulse: online | stale | offline

Telemetria NÃO participa do estado operacional: device offline não significa
máquina parada. Esta camada só define estados, origens e invariantes de
integridade — a máquina de transição chega na Etapa 02.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from production_control_app.domain.errors import InvalidMesEvent


class WorkCenterOperationalState(StrEnum):
    """Estado operacional MES do centro de trabalho (fato persistido)."""

    IDLE = "idle"
    SETUP = "setup"
    PRODUCING = "producing"
    STOPPED = "stopped"
    PLANNED_STOP = "planned_stop"


STATE_EVENT_SOURCES = frozenset({"operator", "system", "recovery", "integration"})
DOWNTIME_SOURCES = frozenset(
    {"operator_pause", "automatic_detection", "system", "integration", "recovery"}
)
DOWNTIME_CONFIRMER_TYPES = frozenset({"operator", "user", "system"})


def normalize_state(value: object) -> WorkCenterOperationalState:
    """Converte texto para o estado canônico; rejeita valores fora do domínio."""
    try:
        return WorkCenterOperationalState(str(value).strip().lower())
    except (ValueError, AttributeError):
        raise InvalidMesEvent(f"Estado operacional inválido: {value!r}") from None


def normalize_reason_code(value: object) -> str:
    """Código do motivo é identidade estável: sempre minúsculo e aparado."""
    code = str(value or "").strip().lower()
    if not code:
        raise InvalidMesEvent("Código de motivo de parada vazio.")
    if len(code) > 40:
        raise InvalidMesEvent("Código de motivo de parada excede 40 caracteres.")
    return code


def validate_source(value: object, allowed: frozenset[str], *, field: str) -> str:
    source = str(value or "").strip().lower()
    if source not in allowed:
        raise InvalidMesEvent(f"{field} inválido: {value!r}")
    return source


def _require_aware(value: datetime, *, field: str) -> None:
    if value.tzinfo is None:
        raise InvalidMesEvent(f"{field} precisa ser timezone-aware (TIMESTAMPTZ).")


def validate_time_range(
    started_at: datetime, ended_at: datetime | None
) -> None:
    """Invariante temporal: timestamps absolutos e fim nunca antes do início."""
    _require_aware(started_at, field="started_at")
    if ended_at is not None:
        _require_aware(ended_at, field="ended_at")
        if ended_at < started_at:
            raise InvalidMesEvent("ended_at não pode ser anterior a started_at.")


def validate_state_event(event: dict[str, Any]) -> None:
    """Confere um evento de estado antes de persistir (defesa do domínio)."""
    normalize_state(event.get("state"))
    validate_source(event.get("source"), STATE_EVENT_SOURCES, field="source")
    validate_time_range(event["started_at"], event.get("ended_at"))


def validate_downtime_event(event: dict[str, Any]) -> None:
    """Confere uma parada: motivo opcional até a confirmação, nunca depois."""
    validate_source(event.get("source"), DOWNTIME_SOURCES, field="source")
    validate_time_range(event["started_at"], event.get("ended_at"))
    confirmed = bool(event.get("confirmed"))
    reason_code = event.get("reason_code")
    confirmed_at = event.get("confirmed_at")
    if confirmed:
        if reason_code is None:
            raise InvalidMesEvent("Parada confirmada exige motivo classificado.")
        if confirmed_at is None:
            raise InvalidMesEvent("Parada confirmada exige confirmed_at.")
    elif confirmed_at is not None:
        raise InvalidMesEvent("confirmed_at sem confirmed = true é inconsistente.")
