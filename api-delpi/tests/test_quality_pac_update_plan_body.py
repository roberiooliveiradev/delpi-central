from __future__ import annotations

from app.interface.http.routes.quality.action_plans_read_router import UpdateActionPlanBody


def test_update_action_plan_body_accepts_identification_patch_without_status():
    body = UpdateActionPlanBody.model_validate(
        {
            "title": "Plano atualizado",
            "customer_name": "Cliente teste",
            "severity": "medium",
            "branch_code": "01",
            "nonconformity_scope": "internal",
        }
    )

    dumped = body.model_dump(exclude_unset=True)
    assert "status" not in dumped
    assert dumped["title"] == "Plano atualizado"
