from __future__ import annotations

from typing import Any

import pytest

from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginsRepositoryError,
)
from app.infrastructure.persistence.plugins.repositories.audit_5s.postgres_audit_5s_repository import (
    PostgresAudit5sRepository,
)


class AddNcActionProbeRepo(PostgresAudit5sRepository):
    def __init__(self, *, nc_status: str) -> None:
        object.__setattr__(self, "_nc_status", nc_status)
        object.__setattr__(self, "inserted", False)

    def fetch_one(
        self,
        query: str,
        params: tuple[Any, ...] | None = None,
    ) -> dict[str, Any] | None:
        return {"id": "nc-1", "status": self._nc_status}

    def execute_returning_one(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        self.inserted = True
        return {
            "id": "action-1",
            "nonconformity_id": "nc-1",
            "description": "nota",
        }


def test_add_nc_action_rejects_cancelled() -> None:
    repo = AddNcActionProbeRepo(nc_status="cancelled")
    with pytest.raises(PluginsRepositoryError, match="somente visualização"):
        repo.add_nc_action(
            nonconformity_id="nc-1",
            description="Não deveria gravar",
            actor_user_id="user-1",
            actor_display_name="Ana",
        )
    assert repo.inserted is False
