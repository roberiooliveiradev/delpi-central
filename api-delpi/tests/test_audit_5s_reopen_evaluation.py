from __future__ import annotations

from typing import Any

import pytest

from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginsRepositoryError,
)
from app.infrastructure.persistence.plugins.repositories.audit_5s.postgres_audit_5s_repository import (
    PostgresAudit5sRepository,
)


class ReopenEvaluationProbeRepo(PostgresAudit5sRepository):
    def __init__(
        self,
        *,
        status: str = "evaluation_complete",
        exists: bool = True,
        nonconformities: list[dict[str, Any]] | None = None,
    ) -> None:
        object.__setattr__(self, "_status", status)
        object.__setattr__(self, "_exists", exists)
        object.__setattr__(self, "_nonconformities", nonconformities or [])
        object.__setattr__(self, "reopened", False)

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

    def list_nonconformities(self, audit_id: str) -> list[dict[str, Any]]:
        return self._nonconformities

    def execute(self, query: str, params: tuple[Any, ...] | None = None) -> None:
        if "SET status = 'draft'" in query:
            self.reopened = True
            self._status = "draft"


@pytest.mark.parametrize("status", ["evaluation_complete", "nc_in_progress"])
def test_reopen_evaluation_sets_draft(status: str) -> None:
    repo = ReopenEvaluationProbeRepo(status=status)
    result = repo.reopen_evaluation("audit-1")
    assert repo.reopened is True
    assert result["status"] == "draft"


def test_reopen_evaluation_rejects_draft() -> None:
    repo = ReopenEvaluationProbeRepo(status="draft")
    with pytest.raises(PluginsRepositoryError, match="já está em fase de avaliação"):
        repo.reopen_evaluation("audit-1")


def test_reopen_evaluation_rejects_closed() -> None:
    repo = ReopenEvaluationProbeRepo(status="closed")
    with pytest.raises(PluginsRepositoryError, match="encerradas"):
        repo.reopen_evaluation("audit-1")


def test_reopen_evaluation_rejects_when_nonconformities_exist() -> None:
    repo = ReopenEvaluationProbeRepo(
        status="evaluation_complete",
        nonconformities=[{"id": "nc-1"}],
    )
    with pytest.raises(PluginsRepositoryError, match="não conformidades registradas"):
        repo.reopen_evaluation("audit-1")
    assert repo.reopened is False
