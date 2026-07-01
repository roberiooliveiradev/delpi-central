"""Testes — snapshot e use cases de revisão PAC."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.application.use_cases.quality_action_plans.pac_plan_revision_use_cases import (
    GetPlanRevisionUseCase,
    ListPlanRevisionsRequest,
    ListPlanRevisionsUseCase,
    RestorePlanRevisionRequest,
    RestorePlanRevisionUseCase,
)
from app.domain.services.quality_action_plans.pac_plan_revision_snapshot_service import (
    REVISION_SCOPE_CREATED,
    REVISION_SCOPE_IDENTIFICATION,
    build_snapshot_from_detail,
    default_revision_summary,
    plan_fields_for_restore,
    validate_snapshot,
)


def test_build_snapshot_strips_derived_plan_fields() -> None:
    detail = {
        "plan": {
            "id": "p1",
            "title": "NC cliente",
            "was_ever_completed": True,
            "contact_roles": {"quality": "Ana"},
            "sla_level": "warning",
        },
        "actions": [
            {
                "id": "a1",
                "description": "Corrigir processo",
                "created_at": "2026-01-01T00:00:00Z",
            }
        ],
        "evidences": [
            {
                "id": "e1",
                "type": "photo",
                "section": "problem",
                "file_name": "foto.jpg",
                "storage_path": "/volume/secret",
            }
        ],
        "team_members": [
            {
                "member_name": "João",
                "member_user_id": "u1",
                "is_leader": True,
                "sort_order": 1,
            }
        ],
    }

    snapshot = build_snapshot_from_detail(detail)

    assert snapshot["schema_version"] == 1
    assert snapshot["plan"]["title"] == "NC cliente"
    assert "was_ever_completed" not in snapshot["plan"]
    assert "contact_roles" not in snapshot["plan"]
    assert "created_at" not in snapshot["actions"][0]
    assert snapshot["actions"][0]["id"] == "a1"
    assert "storage_path" not in snapshot["evidences"][0]
    assert snapshot["evidences"][0]["file_name"] == "foto.jpg"
    assert snapshot["team_members"][0]["member_name"] == "João"


def test_validate_snapshot_rejects_unsupported_version() -> None:
    with pytest.raises(ValueError, match="Versão de snapshot"):
        validate_snapshot({"schema_version": 99, "plan": {}})


def test_plan_fields_for_restore_excludes_identity_columns() -> None:
    snapshot = build_snapshot_from_detail(
        {
            "plan": {
                "id": "p1",
                "code": "PAC-2026-0001",
                "title": "Título",
                "status": "in_progress",
                "created_at": "2026-01-01",
                "created_by_user_id": "u1",
            }
        }
    )
    fields = plan_fields_for_restore(snapshot)
    assert fields == {"title": "Título", "status": "in_progress"}


def test_default_revision_summary_known_scopes() -> None:
    assert default_revision_summary(REVISION_SCOPE_CREATED) == "Plano criado."
    assert default_revision_summary(REVISION_SCOPE_IDENTIFICATION).startswith("Identificação")
    assert default_revision_summary("unknown") == "Plano atualizado."


def test_list_plan_revisions_clamps_page_size() -> None:
    repo = MagicMock()
    repo.list_plan_revisions.return_value = {"items": [], "pagination": {}}
    use_case = ListPlanRevisionsUseCase(repo)

    use_case.execute(ListPlanRevisionsRequest(plan_id="p1", page=0, page_size=500))

    repo.list_plan_revisions.assert_called_once_with("p1", page=1, page_size=100)


def test_get_plan_revision_rejects_invalid_number() -> None:
    use_case = GetPlanRevisionUseCase(MagicMock())
    with pytest.raises(ValueError, match="revision_number"):
        use_case.execute("p1", 0)


def test_restore_plan_revision_requires_actor() -> None:
    use_case = RestorePlanRevisionUseCase(MagicMock())
    with pytest.raises(ValueError, match="updated_by"):
        use_case.execute(
            RestorePlanRevisionRequest(
                plan_id="p1",
                revision_number=1,
                updated_by="",
            )
        )
