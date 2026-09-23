"""Regressão: publicar catálogo 5S confirmava a versão e o pool fazia rollback."""

from __future__ import annotations

import inspect
from contextlib import contextmanager
from typing import Any

import pytest

from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginsRepositoryError,
)
from app.infrastructure.persistence.plugins.repositories.audit_5s.postgres_audit_5s_repository import (
    PostgresAudit5sRepository,
)


class _PoolRollbackCatalogRepo(PostgresAudit5sRepository):
    """Simula o pool: release sem commit descarta o que estava pendente."""

    def __init__(self) -> None:
        super().__init__()
        self.lease = 0
        self.pending: list[tuple[str, tuple[Any, ...] | None]] = []
        self.committed: list[tuple[str, tuple[Any, ...] | None]] = []

    @contextmanager
    def db(self):
        self.lease += 1
        try:
            yield object()
        finally:
            self.lease -= 1
            if self.lease == 0:
                self.pending.clear()

    def fetch_one(
        self,
        query: str,
        params: tuple[Any, ...] | None = None,
    ) -> dict[str, Any] | None:
        if "MAX(catalog_version)" in query:
            return {"max_version": 3}
        return None

    def fetch_all(
        self,
        query: str,
        params: tuple[Any, ...] | None = None,
    ) -> list[dict[str, Any]]:
        if "audit_5s_sensos" in query:
            return [{"id": f"senso-{order}", "sort_order": order} for order in range(1, 6)]
        return []

    def execute(
        self,
        query: str,
        params: tuple[Any, ...] | None = None,
        *,
        auto_commit: bool = True,
    ) -> None:
        with self.db():
            self.pending.append((query, params))
            if auto_commit:
                self._flush_pending()

    def execute_returning_one(
        self,
        query: str,
        params: tuple[Any, ...] | None = None,
        *,
        auto_commit: bool = True,
    ) -> dict[str, Any] | None:
        with self.db():
            self.pending.append((query, params))
            if auto_commit:
                self._flush_pending()
            branch_code = params[0] if params else "01"
            catalog_version = params[1] if params else 0
            return {
                "id": "pub-1",
                "branch_code": branch_code,
                "catalog_version": catalog_version,
                "published_by_user_id": params[2] if params else None,
                "published_at": "2026-09-23T15:00:00Z",
                "criteria_count": params[3] if params else 0,
                "notes": params[4] if params else None,
            }

    def commit(self) -> None:
        with self.db():
            if self.lease == 1:
                return
            self._flush_pending()

    def rollback(self) -> None:
        with self.db():
            self.pending.clear()

    def _flush_pending(self) -> None:
        self.committed.extend(self.pending)
        self.pending.clear()


def _criteria(*descriptions: str) -> list[dict[str, Any]]:
    prefixes = {1: "U", 2: "O", 3: "L", 4: "P", 5: "D"}
    return [
        {
            "senso_order": order,
            "sort_order": 1,
            "code": f"{prefixes[order]}01",
            "description": descriptions[order - 1],
        }
        for order in range(1, 6)
    ]


def _statements(repo: _PoolRollbackCatalogRepo, table: str) -> list[tuple[Any, ...] | None]:
    return [params for query, params in repo.committed if table in query]


def test_publish_catalog_persists_new_version_for_branch() -> None:
    repo = _PoolRollbackCatalogRepo()
    result = repo.publish_catalog(
        branch_code="01",
        criteria=_criteria(
            "Critério alterado",
            "Organização",
            "Limpeza",
            "Padronização",
            "Disciplina",
        ),
        senso_names=None,
        published_by_user_id="user-1",
    )

    assert result["catalog_version"] == 4
    assert result["criteria_count"] == 5
    criteria_rows = _statements(repo, "audit_5s_criteria")
    assert len(criteria_rows) == 5
    assert criteria_rows[0] is not None
    assert criteria_rows[0][2] == "Critério alterado"
    assert criteria_rows[0][4] == 4
    branch_rows = _statements(repo, "audit_5s_branch_catalog")
    assert branch_rows == [("01", 4)]
    publications = _statements(repo, "audit_5s_catalog_publications")
    assert publications == [("01", 4, "user-1", 5, None)]


def test_publish_catalog_persists_senso_names_for_sibling_branch() -> None:
    repo = _PoolRollbackCatalogRepo()
    result = repo.publish_catalog(
        branch_code="02",
        criteria=_criteria(*[f"Senso {order}" for order in range(1, 6)]),
        senso_names=[{"senso_sort_order": 5, "name": "Autodisciplina"}],
        published_by_user_id="user-2",
        notes="ajuste de nome",
    )

    assert result["catalog_version"] == 4
    assert result["branch_code"] == "02"
    senso_rows = _statements(repo, "audit_5s_catalog_senso_names")
    assert senso_rows == [(4, 5, "Autodisciplina")]
    assert _statements(repo, "audit_5s_branch_catalog") == [("02", 4)]


def test_publish_catalog_rolls_back_when_senso_is_unknown() -> None:
    repo = _PoolRollbackCatalogRepo()
    criteria = _criteria(*[f"Senso {order}" for order in range(1, 6)])
    criteria[0]["senso_order"] = 9

    with pytest.raises(PluginsRepositoryError, match="Senso 9"):
        repo.publish_catalog(
            branch_code="01",
            criteria=criteria,
            senso_names=[{"senso_sort_order": 1, "name": "Não deve gravar"}],
            published_by_user_id="user-1",
        )

    assert repo.committed == []


def test_new_audit_reads_published_catalog_existing_audit_keeps_snapshot() -> None:
    create_src = inspect.getsource(PostgresAudit5sRepository.create_audit)
    get_src = inspect.getsource(PostgresAudit5sRepository.get_audit)
    assert "resolve_catalog_version(branch_code)" in create_src
    assert 'list_criteria_catalog(int(audit["catalog_version"]))' in get_src
