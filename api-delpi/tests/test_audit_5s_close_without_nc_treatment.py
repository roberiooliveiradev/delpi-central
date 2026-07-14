from __future__ import annotations

from typing import Any

import pytest

from app.domain.services.audit_5s.audit_5s_status import (
    AUDIT_STATUS_CLOSED_WITHOUT_NC_TREATMENT,
    is_audit_closed,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginsRepositoryError,
)
from app.infrastructure.persistence.plugins.repositories.audit_5s.postgres_audit_5s_repository import (
    PostgresAudit5sRepository,
)
from app.application.security import api_delpi_permissions as perms


class CloseWithoutNcProbeRepo(PostgresAudit5sRepository):
    def __init__(
        self,
        *,
        status: str = "nc_in_progress",
        exists: bool = True,
    ) -> None:
        object.__setattr__(self, "_status", status)
        object.__setattr__(self, "_exists", exists)
        object.__setattr__(self, "executed", [])
        object.__setattr__(self, "committed", False)
        object.__setattr__(self, "rolled_back", False)

    def get_audit(self, audit_id: str) -> dict[str, Any] | None:
        if not self._exists:
            return None
        return {
            "id": audit_id,
            "status": self._status,
            "branch_code": "01",
            "audit_code": "A5S-TEST",
        }

    def execute(
        self,
        query: str,
        params: tuple[Any, ...] | None = None,
        *,
        auto_commit: bool = True,
    ) -> None:
        self.executed.append((query, params, auto_commit))
        if "SET status = %s" in query and params:
            self._status = str(params[0])

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True


def test_is_audit_closed_includes_without_nc_treatment() -> None:
    assert is_audit_closed("closed")
    assert is_audit_closed("closed_without_nc_treatment")
    assert not is_audit_closed("nc_in_progress")


@pytest.mark.parametrize("status", ["evaluation_complete", "nc_in_progress"])
def test_close_without_nc_treatment_cancels_open_ncs_and_sets_status(status: str) -> None:
    repo = CloseWithoutNcProbeRepo(status=status)
    result = repo.close_audit_without_nc_treatment("audit-1")

    assert result["status"] == AUDIT_STATUS_CLOSED_WITHOUT_NC_TREATMENT
    assert repo.committed is True
    assert any("audit_5s_nonconformities" in query for query, *_ in repo.executed)
    assert any(
        params and params[0] == AUDIT_STATUS_CLOSED_WITHOUT_NC_TREATMENT
        for _, params, _ in repo.executed
    )


@pytest.mark.parametrize("status", ["draft", "closed", "closed_without_nc_treatment"])
def test_close_without_nc_treatment_rejects_invalid_status(status: str) -> None:
    repo = CloseWithoutNcProbeRepo(status=status)
    with pytest.raises(PluginsRepositoryError):
        repo.close_audit_without_nc_treatment("audit-1")
    assert repo.committed is False


def test_close_without_nc_treatment_not_found() -> None:
    repo = CloseWithoutNcProbeRepo(exists=False)
    with pytest.raises(PluginsRepositoryError, match="não encontrada"):
        repo.close_audit_without_nc_treatment("missing")


def test_admin_permission_constant_and_list() -> None:
    assert perms.AUDITORIA_5S_ADMIN_FILIAL_01 == "auditoria-5s.admin.filial-01"
    assert perms.AUDITORIA_5S_ADMIN_FILIAL_02 == "auditoria-5s.admin.filial-02"
    assert perms.AUDITORIA_5S_ADMIN_FILIAL_01 in perms.AUDIT_5S_ADMIN_PERMISSIONS
    assert perms.AUDITORIA_5S_ADMIN_FILIAL_02 in perms.AUDIT_5S_READ_PERMISSIONS
