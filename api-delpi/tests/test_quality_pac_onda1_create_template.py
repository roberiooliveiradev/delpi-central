from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.application.use_cases.quality_action_plans.quality_action_plans_use_cases import (
    UpdateQualityActionPlanRequest,
    UpdateQualityActionPlanUseCase,
)


def test_create_plan_can_set_customer_template_via_update():
    captured: dict = {}

    class _Repo:
        def update_plan(self, plan_id, fields):
            captured["fields"] = fields
            return {"id": plan_id, "customer_template": fields.get("customer_template")}

    use_case = UpdateQualityActionPlanUseCase(_Repo())
    result = use_case.execute(
        "plan-id",
        UpdateQualityActionPlanRequest(
            customer_template="rnc_8d",
            client_nc_registry="ANON-CREATE",
        ),
        updated_by="user-1",
    )

    assert result is not None
    assert captured["fields"]["customer_template"] == "rnc_8d"
    assert captured["fields"]["client_nc_registry"] == "ANON-CREATE"
