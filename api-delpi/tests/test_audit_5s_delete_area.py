"""Regras de exclusão de área 5S (sem auditorias / sem subáreas)."""

from __future__ import annotations

import pytest

from app.domain.services.audit_5s.audit_5s_area_hierarchy_service import (
    AREA_DELETE_HAS_AUDITS_MESSAGE,
    AREA_DELETE_HAS_CHILDREN_MESSAGE,
    AREA_NOT_FOUND_MESSAGE,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginsRepositoryError,
)
from app.infrastructure.persistence.plugins.repositories.audit_5s.postgres_audit_5s_repository import (
    PostgresAudit5sRepository,
)


def _repo(
    *,
    area: dict | None,
    audit_count: int = 0,
) -> PostgresAudit5sRepository:
    repo = PostgresAudit5sRepository.__new__(PostgresAudit5sRepository)
    repo.get_area = lambda _area_id: area  # type: ignore[method-assign]
    repo.count_audits_for_area = lambda _area_id: audit_count  # type: ignore[method-assign]
    repo._deleted = False

    def _execute(*_args, **_kwargs):
        repo._deleted = True

    repo.execute = _execute  # type: ignore[method-assign]
    return repo


def test_delete_area_positive_unused_leaf() -> None:
    repo = _repo(
        area={
            "id": "a1",
            "branch_code": "02",
            "name": "Folha",
            "children_count": 0,
        }
    )
    repo.delete_area("a1")
    assert repo._deleted is True


def test_delete_area_sibling_empty_aggregator() -> None:
    repo = _repo(
        area={
            "id": "p1",
            "branch_code": "02",
            "name": "Agregadora vazia",
            "children_count": 0,
            "is_aggregator": False,
        }
    )
    repo.delete_area("p1")
    assert repo._deleted is True


def test_delete_area_negative_has_audits() -> None:
    repo = _repo(
        area={"id": "a1", "children_count": 0, "name": "Usada"},
        audit_count=2,
    )
    with pytest.raises(PluginsRepositoryError, match="auditorias"):
        repo.delete_area("a1")
    assert repo._deleted is False
    assert AREA_DELETE_HAS_AUDITS_MESSAGE


def test_delete_area_negative_has_children() -> None:
    repo = _repo(
        area={"id": "p1", "children_count": 3, "name": "Agregadora"},
        audit_count=0,
    )
    with pytest.raises(PluginsRepositoryError, match="subáreas"):
        repo.delete_area("p1")
    assert repo._deleted is False
    assert AREA_DELETE_HAS_CHILDREN_MESSAGE


def test_delete_area_not_found() -> None:
    repo = _repo(area=None)
    with pytest.raises(PluginsRepositoryError, match=AREA_NOT_FOUND_MESSAGE):
        repo.delete_area("missing")
