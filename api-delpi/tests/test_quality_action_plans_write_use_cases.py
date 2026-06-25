from __future__ import annotations

import pytest

from app.application.use_cases.quality_action_plans.quality_action_plans_use_cases import (
    UpdateQualityActionPlanStatusUseCase,
    UpdateQualityActionPlanUseCase,
    UpdateQualityActionPlanRequest,
)
from app.domain.services.quality_action_plans.pac_quality_branch_service import (
    build_recurrence_key,
    validate_branch_code,
)


def test_validate_branch_code_requires_value():
    with pytest.raises(ValueError, match="branch_code"):
        validate_branch_code(None, required=True)


def test_validate_branch_code_normalizes_single_digit():
    assert validate_branch_code("1") == "01"


def test_build_recurrence_key_includes_branch():
    key = build_recurrence_key(
        branch_code="02",
        product_code="90261805",
        failure_mode="trinca",
        explicit=None,
    )
    assert key == "filial:02|produto:90261805|falha:trinca"


def test_update_status_rejects_invalid_status():
    class _Repo:
        def update_plan_status(self, *args, **kwargs):
            raise AssertionError("should not be called")

    use_case = UpdateQualityActionPlanStatusUseCase(_Repo())
    with pytest.raises(ValueError, match="status inválido"):
        use_case.execute("plan-id", status="invalid", updated_by="user-1")


def test_update_plan_rejects_invalid_template():
    class _Repo:
        def update_plan(self, *args, **kwargs):
            raise AssertionError("should not be called")

    use_case = UpdateQualityActionPlanUseCase(_Repo())
    with pytest.raises(ValueError, match="customer_template"):
        use_case.execute(
            "plan-id",
            UpdateQualityActionPlanRequest(customer_template="invalid"),
            updated_by="user-1",
        )


def test_update_plan_delegates_to_repository():
    class _Repo:
        def __init__(self):
            self.called = False

        def update_plan(self, plan_id, fields):
            self.called = True
            assert plan_id == "plan-id"
            assert fields["title"] == "Novo título"
            return {"id": plan_id, "title": "Novo título"}

    repo = _Repo()
    use_case = UpdateQualityActionPlanUseCase(repo)
    result = use_case.execute(
        "plan-id",
        UpdateQualityActionPlanRequest(title="Novo título"),
        updated_by="user-1",
    )
    assert repo.called
    assert result["title"] == "Novo título"
