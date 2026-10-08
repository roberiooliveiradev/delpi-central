"""Aviso realtime de Operator Feedback — somente hint, nunca fonte de verdade.

Reutiliza as salas por filial do MachineLoadRealtimeHub: o cockpit refaz a
leitura HTTP ao receber operator_feedback_updated. Payload mínimo — nunca
note, operador, tokens ou dados sensíveis no socket.

reason preparado para o lifecycle inteiro (created/acknowledged/resolved);
a C2 só emite created — acknowledge/resolve chegam com as rotas do PCP.
"""

from __future__ import annotations

from typing import Any

from production_control_app.application.services.machine_load_realtime_hub import (
    machine_load_realtime_hub,
)

OPERATOR_FEEDBACK_UPDATED = "operator_feedback_updated"


def notify_operator_feedback_changed(
    *,
    branch: str,
    reason: str,
    feedback: dict[str, Any],
) -> None:
    room = str(branch or "").strip()
    if not room or not feedback:
        return
    machine_load_realtime_hub.schedule_broadcast(
        room,
        {
            "type": OPERATOR_FEEDBACK_UPDATED,
            "reason": str(reason or "").strip() or "created",
            "branch": room,
            "feedbackId": feedback.get("id"),
            "productionOrder": feedback.get("production_order"),
            "operationCode": feedback.get("operation_code"),
            "status": feedback.get("status"),
        },
    )
