from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

import pytest

from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginsRepositoryError,
)
from app.infrastructure.persistence.plugins.repositories.audit_5s.postgres_audit_5s_repository import (
    PostgresAudit5sRepository,
)


class ForceCloseNcProbeRepo(PostgresAudit5sRepository):
    def __init__(
        self,
        *,
        nc_status: str = "open",
        exists_nc: bool = True,
    ) -> None:
        object.__setattr__(self, "_nc_status", nc_status)
        object.__setattr__(self, "_exists_nc", exists_nc)
        object.__setattr__(self, "executed", [])
        object.__setattr__(self, "committed", False)

    @contextmanager
    def db(self) -> Iterator[None]:
        yield None

    def fetch_one(
        self,
        query: str,
        params: tuple[Any, ...] | None = None,
    ) -> dict[str, Any] | None:
        if "audit_5s_nonconformities" in query:
            if not self._exists_nc:
                return None
            return {
                "id": "nc-1",
                "audit_id": "audit-1",
                "status": self._nc_status,
            }
        return None

    def _update_nonconformity_row(self, **kwargs: Any) -> dict[str, Any]:
        self.executed.append(("update_nc", kwargs))
        return {"id": "nc-1", "audit_id": "audit-1", "status": "cancelled"}

    def execute(self, query: str, params: tuple[Any, ...] | None = None, **kwargs: Any) -> None:
        self.executed.append(("execute", query.strip(), params))

    def commit(self) -> None:
        self.committed = True

    def _get_nonconformity_by_id(self, nonconformity_id: str) -> dict[str, Any]:
        return {
            "id": nonconformity_id,
            "audit_id": "audit-1",
            "status": "cancelled",
        }


def test_force_close_nc_without_treatment_cancels_open_nc() -> None:
    repo = ForceCloseNcProbeRepo(nc_status="open")
    result = repo.force_close_nc_without_treatment(
        nonconformity_id="nc-1",
        actor_user_id="user-1",
    )

    assert result["status"] == "cancelled"
    assert repo.committed is True
    assert any(
        entry[0] == "execute" and "cancelled_without_treatment" in entry[1]
        for entry in repo.executed
    )


@pytest.mark.parametrize("nc_status", ["in_progress"])
def test_force_close_nc_without_treatment_accepts_in_progress(nc_status: str) -> None:
    repo = ForceCloseNcProbeRepo(nc_status=nc_status)
    result = repo.force_close_nc_without_treatment(
        nonconformity_id="nc-1",
        actor_user_id="user-1",
    )
    assert result["status"] == "cancelled"


@pytest.mark.parametrize("nc_status", ["closed", "cancelled"])
def test_force_close_nc_without_treatment_rejects_terminal(nc_status: str) -> None:
    repo = ForceCloseNcProbeRepo(nc_status=nc_status)
    with pytest.raises(PluginsRepositoryError):
        repo.force_close_nc_without_treatment(
            nonconformity_id="nc-1",
            actor_user_id="user-1",
        )


def test_force_close_nc_without_treatment_not_found() -> None:
    repo = ForceCloseNcProbeRepo(exists_nc=False)
    with pytest.raises(PluginsRepositoryError, match="não encontrada"):
        repo.force_close_nc_without_treatment(
            nonconformity_id="missing",
            actor_user_id="user-1",
        )
