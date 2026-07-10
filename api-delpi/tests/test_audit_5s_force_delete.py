from __future__ import annotations

from typing import Any

import pytest

from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginsRepositoryError,
)
from app.infrastructure.persistence.plugins.repositories.audit_5s.postgres_audit_5s_repository import (
    PostgresAudit5sRepository,
)


class ForceDeleteProbeRepo(PostgresAudit5sRepository):
    def __init__(self, *, status: str = "draft", exists: bool = True) -> None:
        object.__setattr__(self, "_status", status)
        object.__setattr__(self, "_exists", exists)
        object.__setattr__(self, "purged_audit_id", None)
        object.__setattr__(self, "deleted_audit_id", None)

    def get_audit_delete_target(self, audit_id: str) -> dict[str, Any] | None:
        if not self._exists:
            return None
        return {
            "id": audit_id,
            "status": self._status,
            "branch_code": "01",
            "audit_code": "A5S-TEST",
        }

    def purge_audit_files(self, audit_id: str) -> None:
        self.purged_audit_id = audit_id

    def execute(self, query: str, params: tuple[Any, ...] | None = None) -> None:
        if "DELETE FROM quality.audit_5s_audits" in query:
            self.deleted_audit_id = params[0] if params else None


@pytest.mark.parametrize("status", ["draft", "evaluation_complete", "nc_in_progress", "closed"])
def test_force_delete_audit_removes_any_status(status: str) -> None:
    repo = ForceDeleteProbeRepo(status=status)
    repo.force_delete_audit("audit-1")
    assert repo.purged_audit_id == "audit-1"
    assert repo.deleted_audit_id == "audit-1"


@pytest.mark.parametrize("status", ["evaluation_complete", "nc_in_progress", "closed"])
def test_delete_audit_rejects_non_draft(status: str) -> None:
    repo = ForceDeleteProbeRepo(status=status)
    with pytest.raises(PluginsRepositoryError, match="em avaliação"):
        repo.delete_audit("audit-1")
    assert repo.purged_audit_id is None
    assert repo.deleted_audit_id is None


def test_delete_audit_allows_draft() -> None:
    repo = ForceDeleteProbeRepo(status="draft")
    repo.delete_audit("audit-1")
    assert repo.purged_audit_id == "audit-1"
    assert repo.deleted_audit_id == "audit-1"


def test_force_delete_audit_not_found() -> None:
    repo = ForceDeleteProbeRepo(exists=False)
    with pytest.raises(PluginsRepositoryError, match="não encontrada"):
        repo.force_delete_audit("missing")
