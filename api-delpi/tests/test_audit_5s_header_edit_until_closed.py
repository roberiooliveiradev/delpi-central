from __future__ import annotations

from typing import Any

import pytest

from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginsRepositoryError,
)
from app.infrastructure.persistence.plugins.repositories.audit_5s.postgres_audit_5s_repository import (
    PostgresAudit5sRepository,
)


class HeaderEditProbeRepo(PostgresAudit5sRepository):
    def __init__(self, status: str) -> None:
        object.__setattr__(self, "_status", status)

    def fetch_one(self, query: str, params: tuple[Any, ...] | None = None) -> dict[str, Any] | None:
        if "audit_5s_audits" in query:
            return {"id": "audit-1", "status": self._status, "branch_code": "02"}
        return None


@pytest.mark.parametrize("status", ["draft", "evaluation_complete", "nc_in_progress"])
def test_update_audit_allows_header_edit_until_closed(status: str) -> None:
    repo = HeaderEditProbeRepo(status)
    with pytest.raises(PluginsRepositoryError) as exc:
        # Sem área/campos suficientes cai em "Nenhuma alteração" ou validação seguinte —
        # o importante é não bloquear pelo status antes disso.
        repo.update_audit(audit_id="audit-1")
    assert "encerrada" not in str(exc.value).lower()
    assert "em avaliação" not in str(exc.value).lower()


def test_update_audit_blocks_header_when_closed() -> None:
    repo = HeaderEditProbeRepo("closed")
    with pytest.raises(PluginsRepositoryError, match="encerrada"):
        repo.update_audit(audit_id="audit-1", audit_date="2026-07-08")
