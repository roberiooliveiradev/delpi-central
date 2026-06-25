from __future__ import annotations

import pytest

from app.application.use_cases.quality_action_plans.quality_action_plans_use_cases import (
    UpdateQualityActionPlanRequest,
    UpdateQualityActionPlanUseCase,
)
from app.domain.services.quality_action_plans.quality_action_plan_serialization import (
    serialize_plan_row,
)


def test_serialize_plan_row_exposes_linked_audit_5s_nc_id():
    row = {
        "id": "11111111-1111-1111-1111-111111111111",
        "code": "PAC-2026-0001",
        "title": "Teste",
        "linked_audit_5s_nc_id": "44444444-4444-4444-4444-444444444444",
        "symptom_tags": [],
        "template_payload": {},
        "severity": "medium",
        "status": "triage",
    }

    result = serialize_plan_row(row)

    assert result["linked_audit_5s_nc_id"] == "44444444-4444-4444-4444-444444444444"


def test_update_plan_passes_linked_audit_5s_nc_id_to_repository():
    captured: dict = {}

    class _Repo:
        def update_plan(self, plan_id, fields):
            captured["fields"] = fields
            return {"id": plan_id}

    nc_id = "55555555-5555-5555-5555-555555555555"
    use_case = UpdateQualityActionPlanUseCase(_Repo())
    use_case.execute(
        "plan-id",
        UpdateQualityActionPlanRequest(linked_audit_5s_nc_id=nc_id),
        updated_by="user-1",
    )

    assert captured["fields"]["linked_audit_5s_nc_id"] == nc_id


def test_update_plan_clears_linked_audit_5s_nc_id_when_explicit_null():
    captured: dict = {}

    class _Repo:
        def update_plan(self, plan_id, fields):
            captured["fields"] = fields
            return {"id": plan_id}

    use_case = UpdateQualityActionPlanUseCase(_Repo())
    use_case.execute(
        "plan-id",
        UpdateQualityActionPlanRequest(linked_audit_5s_nc_id=None),
        updated_by="user-1",
        explicit_fields=frozenset({"linked_audit_5s_nc_id"}),
    )

    assert captured["fields"]["linked_audit_5s_nc_id"] is None
