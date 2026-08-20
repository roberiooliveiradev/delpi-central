from __future__ import annotations

from production_control_app.application.services.machine_load_realtime_hub import (
    machine_load_realtime_hub,
)

MACHINE_LOAD_UPDATED = "machine_load_updated"


def notify_machine_load_changed(
    *,
    branch: str,
    reason: str,
    work_center: str | None = None,
) -> None:
    """Avisa os cockpits conectados na filial que a fila mudou (`reason`: sequence/refresh)."""
    room = str(branch or "").strip()
    if not room:
        return
    machine_load_realtime_hub.schedule_broadcast(
        room,
        {
            "type": MACHINE_LOAD_UPDATED,
            "reason": reason,
            "branch": room,
            "workCenter": work_center or None,
        },
    )
