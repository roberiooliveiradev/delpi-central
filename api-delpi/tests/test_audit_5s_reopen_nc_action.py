from __future__ import annotations

from typing import Any

import pytest

from app.domain.services.audit_5s.audit_5s_status import AUDIT_STATUS_NC_IN_PROGRESS
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginsRepositoryError,
)
from app.infrastructure.persistence.plugins.repositories.audit_5s.postgres_audit_5s_repository import (
    PostgresAudit5sRepository,
)


class ReopenNcActionProbeRepo(PostgresAudit5sRepository):
    def __init__(
        self,
        *,
        nc_status: str = "closed",
        audit_status: str = "closed",
        exists_nc: bool = True,
        exists_audit: bool = True,
    ) -> None:
        object.__setattr__(self, "_nc_status", nc_status)
        object.__setattr__(self, "_audit_status", audit_status)
        object.__setattr__(self, "_exists_nc", exists_nc)
        object.__setattr__(self, "_exists_audit", exists_audit)
        object.__setattr__(self, "executed", [])
        object.__setattr__(self, "committed", False)
        object.__setattr__(self, "nc_new_status", None)
        object.__setattr__(self, "audit_new_status", None)

    def fetch_one(
        self,
        query: str,
        params: tuple[Any, ...] | None = None,
    ) -> dict[str, Any] | None:
        if "audit_5s_nonconformities" in query and "audit_id" in query:
            if not self._exists_nc:
                return None
            return {
                "id": "nc-1",
                "audit_id": "audit-1",
                "status": self._nc_status,
            }
        if "audit_5s_audits" in query:
            if not self._exists_audit:
                return None
            return {
                "id": "audit-1",
                "status": self._audit_status,
            }
        return None

    def _update_nonconformity_row(
        self,
        *,
        nonconformity_id: str,
        updates: list[str],
        params: list[Any],
    ) -> dict[str, Any] | None:
        self.nc_new_status = params[0] if params else None
        self._nc_status = str(self.nc_new_status)
        return {
            "id": nonconformity_id,
            "audit_id": "audit-1",
            "status": self._nc_status,
        }

    def _get_nonconformity_by_id(self, nonconformity_id: str) -> dict[str, Any] | None:
        return {
            "id": nonconformity_id,
            "audit_id": "audit-1",
            "status": self._nc_status,
        }

    def execute(
        self,
        query: str,
        params: tuple[Any, ...] | None = None,
        *,
        auto_commit: bool = True,
    ) -> None:
        self.executed.append((query, params, auto_commit))
        if "UPDATE quality.audit_5s_audits" in query and params:
            self.audit_new_status = params[0]
            self._audit_status = str(params[0])

    def commit(self) -> None:
        self.committed = True


def test_reopen_nc_action_sets_in_progress_and_reopens_closed_audit() -> None:
    repo = ReopenNcActionProbeRepo(nc_status="closed", audit_status="closed")
    result = repo.reopen_nc_action(nonconformity_id="nc-1", actor_user_id="user-1")

    assert result["status"] == "in_progress"
    assert repo.nc_new_status == "in_progress"
    assert repo.audit_new_status == AUDIT_STATUS_NC_IN_PROGRESS
    assert repo.committed is True
    assert any("action_reopened" in query for query, *_ in repo.executed)


@pytest.mark.parametrize(
    "audit_status",
    ["closed_without_nc_treatment", "evaluation_complete"],
)
def test_reopen_nc_action_moves_audit_to_nc_in_progress(audit_status: str) -> None:
    repo = ReopenNcActionProbeRepo(nc_status="closed", audit_status=audit_status)
    repo.reopen_nc_action(nonconformity_id="nc-1", actor_user_id="user-1")
    assert repo.audit_new_status == AUDIT_STATUS_NC_IN_PROGRESS


def test_reopen_nc_action_keeps_audit_when_already_nc_in_progress() -> None:
    repo = ReopenNcActionProbeRepo(nc_status="closed", audit_status="nc_in_progress")
    repo.reopen_nc_action(nonconformity_id="nc-1", actor_user_id="user-1")
    assert repo.audit_new_status is None
    assert repo.committed is True


@pytest.mark.parametrize("nc_status", ["open", "in_progress", "cancelled"])
def test_reopen_nc_action_rejects_non_closed(nc_status: str) -> None:
    repo = ReopenNcActionProbeRepo(nc_status=nc_status)
    with pytest.raises(PluginsRepositoryError, match="concluídas"):
        repo.reopen_nc_action(nonconformity_id="nc-1", actor_user_id="user-1")
    assert repo.committed is False


def test_reopen_nc_action_not_found() -> None:
    repo = ReopenNcActionProbeRepo(exists_nc=False)
    with pytest.raises(PluginsRepositoryError, match="não encontrada"):
        repo.reopen_nc_action(nonconformity_id="missing", actor_user_id="user-1")
