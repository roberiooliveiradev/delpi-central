from __future__ import annotations

from pathlib import Path


def test_action_plans_router_defines_update_status_body_model():
    router_path = (
        Path(__file__).resolve().parents[1]
        / "app/interface/http/routes/quality/action_plans_read_router.py"
    )
    source = router_path.read_text(encoding="utf-8")
    assert "class UpdateActionPlanStatusBody(BaseModel):" in source
    assert 'update_action_plan_status(plan_id: str, body: UpdateActionPlanStatusBody' in source
