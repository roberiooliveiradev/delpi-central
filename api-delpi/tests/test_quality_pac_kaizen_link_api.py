from __future__ import annotations

import pytest

from app.application.use_cases.quality_action_plans.quality_action_plans_use_cases import (
    UpdateQualityActionPlanRequest,
    UpdateQualityActionPlanUseCase,
)
from app.domain.services.quality_action_plans.quality_action_plan_serialization import (
    serialize_plan_row,
)


def test_serialize_plan_row_exposes_linked_kaizen_id():
    row = {
        "id": "11111111-1111-1111-1111-111111111111",
        "code": "PAC-2026-0001",
        "title": "Teste",
        "linked_kaizen_id": "22222222-2222-2222-2222-222222222222",
        "symptom_tags": [],
        "template_payload": {},
        "severity": "medium",
        "status": "triage",
    }

    result = serialize_plan_row(row)

    assert result["linked_kaizen_id"] == "22222222-2222-2222-2222-222222222222"


def test_update_plan_rejects_blank_linked_kaizen_id():
    class _Repo:
        def update_plan(self, *args, **kwargs):
            raise AssertionError("should not be called")

    use_case = UpdateQualityActionPlanUseCase(_Repo())
    with pytest.raises(ValueError, match="linked_kaizen_id"):
        use_case.execute(
            "plan-id",
            UpdateQualityActionPlanRequest(linked_kaizen_id="   "),
            updated_by="user-1",
        )


def test_update_plan_passes_linked_kaizen_id_to_repository():
    captured: dict = {}

    class _Repo:
        def update_plan(self, plan_id, fields):
            captured["plan_id"] = plan_id
            captured["fields"] = fields
            return {"id": plan_id, "linked_kaizen_id": fields["linked_kaizen_id"]}

    kaizen_id = "33333333-3333-3333-3333-333333333333"
    use_case = UpdateQualityActionPlanUseCase(_Repo())
    result = use_case.execute(
        "plan-id",
        UpdateQualityActionPlanRequest(linked_kaizen_id=kaizen_id),
        updated_by="user-1",
    )

    assert result["linked_kaizen_id"] == kaizen_id
    assert captured["fields"]["linked_kaizen_id"] == kaizen_id


def test_update_plan_clears_linked_kaizen_id_when_explicit_null():
    captured: dict = {}

    class _Repo:
        def update_plan(self, plan_id, fields):
            captured["fields"] = fields
            return {"id": plan_id}

    use_case = UpdateQualityActionPlanUseCase(_Repo())
    use_case.execute(
        "plan-id",
        UpdateQualityActionPlanRequest(linked_kaizen_id=None),
        updated_by="user-1",
        explicit_fields=frozenset({"linked_kaizen_id"}),
    )

    assert captured["fields"]["linked_kaizen_id"] is None
