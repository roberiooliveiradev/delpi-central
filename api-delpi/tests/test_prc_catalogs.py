"""PRC engineering catalogs — allowlist, SQL sources, limits."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.interface.http.routes.engineering import prc_catalogs_router
from app.infrastructure.persistence.totvs.engineering_repositories.prc_catalogs_repository import (
    PRC_CATALOG_KINDS,
    PrcCatalogsRepository,
)
from delpi_auth.request_context import clear_current_user, set_current_user


class _FakeRepo(PrcCatalogsRepository):
    def __init__(self, rows=None):
        self.queries: list[tuple[str, tuple]] = []
        self._rows = rows or []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute_query(self, query, params=()):
        self.queries.append((query, tuple(params)))
        return self._rows


def _row(code="01", label="UNIDADE"):
    return {"code": code, "label": label, "disabled": 0}


class TestRepositorySql:
    @pytest.mark.parametrize(
        "catalog,table",
        [
            ("product-groups", "SBM010"),
            ("units", "SAH010"),
            ("warehouses", "NNR010"),
            ("accounting-accounts", "CT1010"),
        ],
    )
    def test_catalog_sql_uses_allowlisted_source(self, catalog, table):
        repo = _FakeRepo()
        repo.list_catalog_items(catalog)
        sql = repo.queries[0][0]
        assert f"FROM {table}" in sql
        assert "D_E_L_E_T_" in sql
        assert "SELECT TOP" in sql

    def test_units_uses_ah_unimed_column(self):
        repo = _FakeRepo()
        repo.list_catalog_items("units")
        sql = repo.queries[0][0]
        assert "AH_UNIMED" in sql
        assert "AH_UNIMES" not in sql

    def test_query_filter_is_parameterized(self):
        repo = _FakeRepo()
        repo.list_catalog_items("product-groups", query="plas")
        sql, params = repo.queries[0]
        assert "LIKE ?" in sql
        assert params == ("plas%", "%plas%")

    def test_unknown_catalog_raises(self):
        with pytest.raises(KeyError):
            _FakeRepo().list_catalog_items("unknown-catalog")

    def test_limit_clamped(self):
        repo = _FakeRepo(rows=[_row()])
        items, has_more = repo.list_catalog_items("units", limit=1)
        assert len(items) == 1
        assert has_more is False

    def test_items_are_returned(self):
        repo = _FakeRepo(rows=[_row("PC", "Peça"), _row("UN", "Unidade")])
        items, has_more = repo.list_catalog_items("units")
        assert [i["code"] for i in items] == ["PC", "UN"]
        assert has_more is False


class TestCatalogKinds:
    def test_allowlist_is_complete(self):
        assert set(PRC_CATALOG_KINDS) == {
            "product-groups",
            "units",
            "warehouses",
            "accounting-accounts",
        }


class TestRepositoryIsolation:
    """Regressão D7: o router mantinha ``_CATALOG_REPOSITORY`` singleton.
    ``BaseRepository`` guarda conexão/cursor em ``self`` — com a página
    disparando os 4 catálogos em paralelo, o ``__exit__`` de uma request
    zerava o cursor da outra → ``'NoneType' object has no attribute
    'fetchall'`` → 500 → BFF 503. Cada request deve instanciar o
    repositório."""

    def test_router_creates_fresh_repository_per_request(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        created: list[object] = []

        class _CountingRepo:
            def __init__(self) -> None:
                created.append(self)

            def list_catalog_items(self, catalog, *, query=None, limit=200):
                return [], False

        monkeypatch.setattr(
            prc_catalogs_router, "PrcCatalogsRepository", _CountingRepo
        )
        set_current_user(SimpleNamespace(is_superadmin=True))
        try:
            prc_catalogs_router.list_prc_catalog_items("units")
            prc_catalogs_router.list_prc_catalog_items("product-groups")
        finally:
            clear_current_user()

        assert len(created) == 2
        assert created[0] is not created[1]

    def test_router_module_has_no_shared_repository(self):
        shared = [
            name
            for name, value in vars(prc_catalogs_router).items()
            if isinstance(value, PrcCatalogsRepository)
        ]
        assert shared == []
