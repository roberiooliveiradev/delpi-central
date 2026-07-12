from __future__ import annotations

from datetime import date

import pytest

from app.domain.services.audit_5s.audit_5s_nc_sla_service import (
    is_nc_plan_complete,
    resolve_nc_due_sla,
    resolve_nc_workflow,
)


def test_is_nc_plan_complete_requires_all_fields() -> None:
    row = {
        "description": "Falta organização",
        "root_cause": "Sem rotina",
        "corrective_action": "Treinar equipe",
        "responsible_name": "João",
        "due_date": "2026-07-15",
    }
    assert is_nc_plan_complete(row) is True
    row["root_cause"] = "ab"
    assert is_nc_plan_complete(row) is False


@pytest.mark.parametrize(
    ("status", "due_date", "expected_level", "expected_days"),
    [
        ("closed", "2026-01-01", "none", None),
        ("open", None, "none", None),
        ("open", "2026-07-20", "ok", 10),
        ("in_progress", "2026-07-12", "due_soon", 2),
        ("in_progress", "2026-07-05", "overdue", -5),
    ],
)
def test_resolve_nc_due_sla(
    status: str,
    due_date: str | None,
    expected_level: str,
    expected_days: int | None,
) -> None:
    result = resolve_nc_due_sla(
        status=status,
        due_date=due_date,
        reference=date(2026, 7, 10),
    )
    assert result["due_sla_level"] == expected_level
    assert result["days_until_due"] == expected_days


def test_resolve_nc_workflow_not_started() -> None:
    result = resolve_nc_workflow(
        status="open",
        plan_complete=False,
        has_before_evidence=False,
        has_after_evidence=False,
    )
    assert result == {"plan_started": False, "workflow_step": 1}


def test_resolve_nc_workflow_evidence_step() -> None:
    result = resolve_nc_workflow(
        status="in_progress",
        plan_complete=True,
        has_before_evidence=True,
        has_after_evidence=False,
    )
    assert result == {"plan_started": True, "workflow_step": 2}


def test_resolve_nc_workflow_ready_to_finalize() -> None:
    result = resolve_nc_workflow(
        status="in_progress",
        plan_complete=True,
        has_before_evidence=True,
        has_after_evidence=True,
    )
    assert result == {"plan_started": True, "workflow_step": 3}


def test_serialize_nc_board_item_enriches_workflow_and_sla() -> None:
    from app.infrastructure.persistence.plugins.repositories.audit_5s.postgres_audit_5s_repository import (
        PostgresAudit5sRepository,
    )

    row = {
        "id": "nc-1",
        "audit_id": "audit-1",
        "response_id": "resp-1",
        "description": "Descrição da NC",
        "root_cause": "Causa raiz",
        "corrective_action": "Ação corretiva",
        "responsible_name": "Maria",
        "due_date": date(2026, 7, 5),
        "priority": "high",
        "status": "in_progress",
        "created_at": None,
        "updated_at": None,
        "audit_code": "A5S-001",
        "audit_date": date(2026, 6, 30),
        "branch_code": "01",
        "shift": "TURNO_1",
        "area_name": "Linha 1",
        "criterion_code": "S1-01",
        "criterion_description": "Critério teste",
        "senso_order": 1,
        "senso_name": "Seiri",
        "has_before_evidence": True,
        "has_after_evidence": False,
        "last_action_at": None,
    }
    item = PostgresAudit5sRepository._serialize_nc_board_item(
        PostgresAudit5sRepository(),
        row,
    )
    assert item["audit_code"] == "A5S-001"
    assert item["plan_started"] is True
    assert item["workflow_step"] == 2
    assert item["due_sla_level"] == "overdue"
    assert item["has_before_evidence"] is True
    assert item["has_after_evidence"] is False
    assert item["is_registered"] is True


def test_serialize_nc_board_candidate_item_marks_pending() -> None:
    from app.infrastructure.persistence.plugins.repositories.audit_5s.postgres_audit_5s_repository import (
        PostgresAudit5sRepository,
    )

    row = {
        "response_id": "resp-1",
        "audit_id": "audit-1",
        "observation": "Área desorganizada",
        "score": 1,
        "audit_code": "01-000002",
        "audit_date": date(2026, 7, 10),
        "branch_code": "01",
        "shift": "TURNO_1",
        "area_name": "Linha teste",
        "criterion_code": "S1-01",
        "criterion_description": "Critério pendente",
        "senso_order": 1,
        "senso_name": "Seiri",
    }
    item = PostgresAudit5sRepository()._serialize_nc_board_candidate_item(row)
    assert item["status"] == "pending"
    assert item["is_registered"] is False
    assert item["plan_started"] is False
    assert item["id"] == "candidate:resp-1"
