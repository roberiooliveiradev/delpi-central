from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

import pytest

from app.application.services.audit_5s.scoring_service import (
    is_nc_candidate,
    nc_cleared_by_score,
)
from app.domain.services.audit_5s.audit_5s_status import AUDIT_STATUS_DRAFT
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginsRepositoryError,
)
from app.infrastructure.persistence.plugins.repositories.audit_5s.postgres_audit_5s_repository import (
    PostgresAudit5sRepository,
)


def test_nc_cleared_by_score() -> None:
    assert nc_cleared_by_score(5, False) is True
    assert nc_cleared_by_score(None, True) is True
    assert nc_cleared_by_score(1, False) is False
    assert nc_cleared_by_score(3, False) is False
    assert is_nc_candidate(1, False) is True
    assert is_nc_candidate(5, False) is False


class ReopenEvaluationProbeRepo(PostgresAudit5sRepository):
    def __init__(
        self,
        *,
        status: str = "evaluation_complete",
        exists: bool = True,
    ) -> None:
        object.__setattr__(self, "_status", status)
        object.__setattr__(self, "_exists", exists)
        object.__setattr__(self, "reopened", False)
        object.__setattr__(self, "executed", [])

    @contextmanager
    def db(self) -> Iterator[object]:
        yield object()

    def get_audit(self, audit_id: str) -> dict[str, Any] | None:
        if not self._exists:
            return None
        return {
            "id": audit_id,
            "status": self._status,
            "branch_code": "01",
            "progress": {"total": 48, "scored": 48, "pending": 0},
            "responses": [],
            "criteria": [],
        }

    def execute(
        self,
        query: str,
        params: tuple[Any, ...] | None = None,
        *,
        auto_commit: bool = True,
    ) -> None:
        self.executed.append((query, params, auto_commit))
        if "UPDATE quality.audit_5s_audits" in " ".join(query.split()) and params:
            if params[0] == AUDIT_STATUS_DRAFT:
                self.reopened = True
                self._status = AUDIT_STATUS_DRAFT


class UpsertResponseProbeRepo(PostgresAudit5sRepository):
    def __init__(
        self,
        *,
        linked_nc: dict[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "_linked_nc", linked_nc)
        object.__setattr__(self, "cancelled_nc_ids", [])
        object.__setattr__(self, "executed", [])
        object.__setattr__(self, "_row", {
            "id": "resp-1",
            "criterion_id": "crit-1",
            "score": 5,
            "is_not_applicable": False,
            "observation": None,
            "version": 2,
            "updated_by_user_id": "u1",
            "updated_at": None,
        })

    @contextmanager
    def db(self) -> Iterator[object]:
        yield object()

    def fetch_one(self, query: str, params: tuple[Any, ...] | None = None):
        normalized = " ".join(query.split())
        if "FROM quality.audit_5s_audits" in normalized:
            return {"id": "audit-1", "status": "draft", "catalog_version": 1}
        if "FROM quality.audit_5s_responses" in normalized and "criterion_id" in normalized:
            return {"id": "resp-1", "version": 1}
        if "FROM quality.audit_5s_nonconformities" in normalized:
            return self._linked_nc
        return None

    def execute(
        self,
        query: str,
        params: tuple[Any, ...] | None = None,
        *,
        auto_commit: bool = True,
    ) -> None:
        self.executed.append((query, params, auto_commit))
        if "UPDATE quality.audit_5s_nonconformities" in query and "cancelled" in query:
            self.cancelled_nc_ids.append(str(params[0]) if params else "")

    def execute_returning_one(
        self,
        query: str,
        params: tuple[Any, ...] | None = None,
        *,
        auto_commit: bool = True,
    ):
        self.executed.append((query, params, auto_commit))
        return dict(self._row)

    def _refresh_audit_scores(self, audit_id: str, catalog_version: int) -> None:
        return None

    def get_response_attachment_by_response_id(self, response_id: str):
        return None

    def commit(self) -> None:
        return None

    def rollback(self) -> None:
        return None


@pytest.mark.parametrize("status", ["evaluation_complete", "nc_in_progress"])
def test_reopen_evaluation_sets_draft_without_touching_ncs(status: str) -> None:
    repo = ReopenEvaluationProbeRepo(status=status)
    result = repo.reopen_evaluation("audit-1")
    assert repo.reopened is True
    assert result["status"] == "draft"
    assert not any("audit_5s_nonconformities" in q for q, _p, _a in repo.executed)


def test_reopen_evaluation_rejects_draft() -> None:
    repo = ReopenEvaluationProbeRepo(status="draft")
    with pytest.raises(PluginsRepositoryError, match="já está em fase de avaliação"):
        repo.reopen_evaluation("audit-1")


def test_reopen_evaluation_rejects_closed() -> None:
    repo = ReopenEvaluationProbeRepo(status="closed")
    with pytest.raises(PluginsRepositoryError, match="encerradas"):
        repo.reopen_evaluation("audit-1")


def test_upsert_cancels_open_nc_when_score_clears() -> None:
    repo = UpsertResponseProbeRepo(linked_nc={"id": "nc-1", "status": "open"})
    result = repo.upsert_response(
        audit_id="audit-1",
        criterion_id="crit-1",
        score=5,
        is_not_applicable=False,
        observation=None,
        updated_by_user_id="u1",
        expected_version=1,
    )
    assert result["score"] == 5
    assert repo.cancelled_nc_ids == ["nc-1"]
    assert any("cancelled_after_score_clear" in q for q, _p, _a in repo.executed)


def test_upsert_keeps_nc_when_score_still_candidate() -> None:
    repo = UpsertResponseProbeRepo(linked_nc={"id": "nc-1", "status": "open"})
    repo._row["score"] = 3
    repo.upsert_response(
        audit_id="audit-1",
        criterion_id="crit-1",
        score=3,
        is_not_applicable=False,
        observation=None,
        updated_by_user_id="u1",
        expected_version=1,
    )
    assert repo.cancelled_nc_ids == []


def test_upsert_blocks_clearing_score_when_nc_closed() -> None:
    repo = UpsertResponseProbeRepo(linked_nc={"id": "nc-1", "status": "closed"})
    with pytest.raises(PluginsRepositoryError, match="ação corretiva já foi finalizada"):
        repo.upsert_response(
            audit_id="audit-1",
            criterion_id="crit-1",
            score=5,
            is_not_applicable=False,
            observation=None,
            updated_by_user_id="u1",
            expected_version=1,
        )
    assert repo.cancelled_nc_ids == []
