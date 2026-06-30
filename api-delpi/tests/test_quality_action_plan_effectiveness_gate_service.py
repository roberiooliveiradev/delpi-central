from __future__ import annotations

from app.domain.services.quality_action_plans.quality_action_plan_effectiveness_gate_service import (
    build_incomplete_plan_actions_message,
)


def test_build_incomplete_plan_actions_message_lists_samples():
    message = build_incomplete_plan_actions_message(
        [
            {"id": "act-1", "description": "Revisar processo", "status": "pending"},
            {"id": "act-2", "description": "Validar instrução", "status": "in_progress"},
        ]
    )

    assert "2 ação(ões) não concluída(s)" in message
    assert "Revisar processo" in message
    assert "Pendente" in message
    assert "Em andamento" in message
    assert "quando possível" in message
