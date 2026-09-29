"""Classificação do snapshot de telemetria Pulse (Etapa 05).

Regra de ouro: snapshot não utilizável NUNCA vira ``counter=0`` nem
``counterEpoch=0`` por fallback silencioso — telemetria indisponível não é
máquina parada e não produz contagem artificial.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

PulseSnapshotStatus = Literal["usable", "offline", "invalid", "unavailable"]

_OFFLINE_STATES = {"offline", "stale", "disconnected"}


def _valid_counter(value: Any) -> bool:
    if isinstance(value, bool) or value is None:
        return False
    try:
        return int(value) >= 0
    except (TypeError, ValueError):
        return False


def classify_pulse_snapshot(device: dict[str, Any] | None) -> PulseSnapshotStatus:
    """Classifica o snapshot do contador.

    - ``unavailable``: nenhum snapshot obtido (erro HTTP/exceção tratada fora).
    - ``invalid``: counter/counterEpoch ausentes ou não numéricos.
    - ``offline``: device reportado offline/stale.
    - ``usable``: contador e epoch válidos — seguro para âncora/consolidação.
    """
    if not isinstance(device, dict):
        return "unavailable"
    if not _valid_counter(device.get("counter")) or not _valid_counter(
        device.get("counterEpoch")
    ):
        return "invalid"
    if device.get("online") is False:
        return "offline"
    status = str(device.get("status") or "").strip().lower()
    if status in _OFFLINE_STATES:
        return "offline"
    if _is_stale(device):
        return "offline"
    return "usable"


def _is_stale(device: dict[str, Any]) -> bool:
    """lastSeenAt envelhecido além de 3 ciclos de poll = telemetria velha."""
    last_seen = device.get("lastSeenAt")
    interval = device.get("pollIntervalMs")
    if not last_seen or not isinstance(interval, (int, float)) or interval <= 0:
        return False
    try:
        seen_at = datetime.fromisoformat(str(last_seen).replace("Z", "+00:00"))
    except ValueError:
        return False
    age_ms = (datetime.now(timezone.utc) - seen_at).total_seconds() * 1000
    return age_ms > 3 * float(interval)
