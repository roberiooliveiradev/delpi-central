"""Regressões GLPI #945: fotos opcionais e cancelamento de NC sem plano."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

import pytest

from app.infrastructure.persistence.plugins.plugin_base_repository import PluginsRepositoryError
from app.infrastructure.persistence.plugins.repositories.audit_5s.postgres_audit_5s_repository import (
    PostgresAudit5sRepository,
)


class Ticket945Probe(PostgresAudit5sRepository):
    def __init__(self) -> None:
        object.__setattr__(self, "commands", [])
        object.__setattr__(self, "saved", False)

    @contextmanager
    def db(self) -> Iterator[None]:
        yield None

    def fetch_one(self, query: str, params: tuple[Any, ...] | None = None):
        if "FROM quality.audit_5s_audits" in query:
            return {"id": "audit-1", "status": "evaluation_complete"}
        if "FROM quality.audit_5s_responses" in query:
            return {"id": "response-1", "score": 1, "is_not_applicable": False}
        if "FROM quality.audit_5s_nonconformities" in query:
            return None
        if "FROM quality.audit_5s_nc_candidate_cancellations" in query:
            return None
        return None

    def execute_returning_one(self, query: str, params=None, **kwargs):
        self.commands.append((query, params, kwargs))
        return {
            "id": "cancel-1", "audit_id": "audit-1",
            "response_id": "response-1", "reason": params[3],
            "created_by_user_id": params[4], "created_at": "2026-11-08",
        }

    def commit(self) -> None:
        self.saved = True


def test_cancel_candidate_without_plan_preserves_score_and_reason() -> None:
    repo = Ticket945Probe()
    result = repo.cancel_nc_candidate(
        audit_id="audit-1", response_id="response-1",
        reason="  Não será tratado após consenso  ", actor_user_id="auditor-1",
    )
    assert result["status"] == "cancelled"
    assert result["reason"] == "Não será tratado após consenso"
    assert repo.saved
    assert len(repo.commands) == 1
    assert "INSERT INTO quality.audit_5s_nc_candidate_cancellations" in repo.commands[0][0]
    assert repo.commands[0][2]["auto_commit"] is False


def test_cancel_candidate_rejects_blank_justification() -> None:
    repo = Ticket945Probe()
    with pytest.raises(PluginsRepositoryError, match="justificativa"):
        repo.cancel_nc_candidate(
            audit_id="audit-1", response_id="response-1",
            reason="   ", actor_user_id="auditor-1",
        )
    assert repo.commands == []


def test_low_score_requires_reason_on_write() -> None:
    class EvaluationProbe(Ticket945Probe):
        def fetch_one(self, query: str, params=None):
            if "FROM quality.audit_5s_audits" in query:
                return {"id": "audit-1", "status": "draft"}
            return super().fetch_one(query, params)

    repo = EvaluationProbe()
    with pytest.raises(PluginsRepositoryError, match="motivo"):
        repo.upsert_response(
            audit_id="audit-1", criterion_id="criterion-1",
            score=1, is_not_applicable=False, observation=None,
            updated_by_user_id="auditor-1", expected_version=None,
        )


def test_cancelled_candidate_visible_in_board_with_reason() -> None:
    repo = Ticket945Probe()
    item = repo._serialize_nc_board_candidate_item({
        "response_id": "response-1", "audit_id": "audit-1",
        "score": 1, "observation": "Bancada suja",
        "cancellation_reason": "Reavaliada em reunião",
        "cancelled_at": "2026-11-08T10:00:00",
        "cancelled_by_user_id": "auditor-1",
        "audit_code": "A-001", "audit_date": "2026-11-08",
        "branch_code": "02", "shift": "TURNO_1",
        "area_name": "Corte", "criterion_code": "S1",
        "criterion_description": "Limpeza",
        "senso_order": 1, "senso_name": "Seiri",
    })
    assert item["status"] == "cancelled"
    assert item["is_registered"] is False
    assert item["cancellation_reason"] == "Reavaliada em reunião"


def test_finalization_does_not_require_photo() -> None:
    class CompletionProbe(Ticket945Probe):
        def fetch_one(self, query: str, params=None):
            if "FROM quality.audit_5s_nonconformities" in query:
                return {
                    "id": "nc-1", "audit_id": "audit-1",
                    "description": "NC encontrada", "root_cause": "Falta de padrão",
                    "corrective_action": "Treinar equipe",
                    "responsible_name": "Ana", "due_date": "2026-11-11",
                    "status": "in_progress",
                }
            return super().fetch_one(query, params)

        def _update_nonconformity_row(self, **kwargs):
            return {"id": "nc-1", "audit_id": "audit-1", "status": "closed"}

        def execute(self, *args, **kwargs):
            self.commands.append((args, kwargs))

        def _get_nonconformity_by_id(self, nonconformity_id):
            return {"id": nonconformity_id, "status": "closed"}

    repo = CompletionProbe()
    result = repo.complete_nc_action(nonconformity_id="nc-1", actor_user_id="auditor-1")
    assert result["status"] == "closed"
    assert repo.saved
