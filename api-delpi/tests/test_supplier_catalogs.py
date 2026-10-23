"""Supplier catalogs — allowlist, SQL sources, use case guards."""

from __future__ import annotations

import pytest

from app.application.use_cases.supplies.list_supplier_catalog_items_use_case import (
    ListSupplierCatalogItemsUseCase,
)
from app.infrastructure.persistence.totvs.supplier_repositories.totvs_supplier_catalogs_repository import (
    SUPPLIER_CATALOG_KINDS,
    TotvsSupplierCatalogsRepository,
)


class _FakeRepo(TotvsSupplierCatalogsRepository):
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


def _row(code="001", label="A VISTA", disabled=0):
    return {"code": code, "label": label, "disabled": disabled}


class TestRepositorySql:
    @pytest.mark.parametrize(
        "catalog,table",
        [
            ("states", "SX5010"),
            ("countries", "SYA010"),
            ("bacen-countries", "CCH010"),
            ("payment-conditions", "SE4010"),
            ("payment-methods", "SX5010"),
            ("financial-natures", "SED010"),
            ("accounting-accounts", "CT1010"),
            ("municipalities", "CC2010"),
            # X4.FIELDS.E6 — referências cadastrais
            ("carriers", "SA4010"),
            ("segments", "SX5010"),
            ("administrators", "SAE010"),
            ("employees", "SRA010"),
            ("price-tables", "AIA010"),
            ("customers", "SA1010"),
        ],
    )
    def test_sources_point_to_proven_tables(self, catalog, table):
        repo = _FakeRepo(rows=[_row()])
        repo.list_catalog_items(catalog, state="SC")
        sql, _ = repo.queries[0]
        assert f"FROM {table}" in sql
        assert "D_E_L_E_T_ = ''" in sql
        assert "TOP (" in sql

    def test_sx5_catalogs_pin_the_option_table(self):
        repo = _FakeRepo()
        repo.list_catalog_items("states")
        assert "X5_TABELA = '12'" in repo.queries[0][0]
        repo.list_catalog_items("payment-methods")
        assert "X5_TABELA = '58'" in repo.queries[1][0]

    def test_municipalities_filter_by_state(self):
        repo = _FakeRepo()
        repo.list_catalog_items("municipalities", state="sc")
        sql, params = repo.queries[0]
        assert "CC2_EST = ?" in sql
        assert params[0] == "SC"

    def test_query_matches_code_prefix_and_description(self):
        repo = _FakeRepo()
        repo.list_catalog_items("countries", query="bras")
        sql, params = repo.queries[0]
        assert "LIKE ?" in sql
        assert "Latin1_General_CI_AI" in sql
        assert params[0] == "bras%"
        assert params[1] == "%bras%"

    def test_limit_is_bounded_and_flags_has_more(self):
        repo = _FakeRepo(rows=[_row(str(i)) for i in range(3)])
        items, has_more = repo.list_catalog_items("payment-methods", limit=2)
        assert len(items) == 2
        assert has_more is True
        repo.list_catalog_items("countries", limit=9999)
        sql, _ = repo.queries[-1]
        assert "TOP (501)" in sql  # cap em 500 + 1 para has_more

    def test_codes_keep_leading_zeros(self):
        repo = _FakeRepo(rows=[_row(code="00132 ")])
        items, _ = repo.list_catalog_items("bacen-countries")
        assert items[0]["code"] == "00132"

    def test_blocked_payment_condition_marks_disabled(self):
        repo = _FakeRepo(rows=[_row(code="002", disabled=1)])
        items, _ = repo.list_catalog_items("payment-conditions")
        assert items[0]["disabled"] is True

    def test_order_by_never_repeats_a_column(self):
        """Regressão F5-UX-R3.1 — ORDER BY duplicado derrubava catálogos
        cuja ordenação coincide com a coluna de código (erro SQL 169)."""
        for catalog in SUPPLIER_CATALOG_KINDS:
            repo = _FakeRepo()
            repo.list_catalog_items(catalog, state="SC")
            sql, _ = repo.queries[0]
            order_clause = sql.split("ORDER BY", 1)[1]
            cols = [c.strip() for c in order_clause.strip().split(",")]
            assert len(cols) == len(set(cols)), catalog

    def test_unknown_catalog_raises(self):
        with pytest.raises(KeyError):
            _FakeRepo().list_catalog_items("orders")

    # --- X4.FIELDS.E6 ------------------------------------------------------

    def test_segments_pin_sx5_t3(self):
        repo = _FakeRepo()
        repo.list_catalog_items("segments")
        assert "X5_TABELA = 'T3'" in repo.queries[0][0]

    def test_customers_items_carry_composite_store(self):
        repo = _FakeRepo(
            rows=[{"code": "000001", "store": "06", "label": "WEG", "disabled": 0}]
        )
        items, _ = repo.list_catalog_items("customers")
        assert items[0]["store"] == "06"
        assert items[0]["code"] == "000001"

    def test_customers_code_param_filters_exact_customer(self):
        repo = _FakeRepo()
        repo.list_catalog_items("customers", code="000001")
        sql, params = repo.queries[0]
        assert "A1_COD = ?" in sql
        assert params[0] == "000001"


class TestUseCaseGuards:
    def test_unknown_catalog_is_rejected(self):
        with pytest.raises(ValueError, match="Catálogo desconhecido"):
            ListSupplierCatalogItemsUseCase(_FakeRepo()).execute("orders")

    def test_municipalities_requires_state(self):
        with pytest.raises(ValueError, match="state"):
            ListSupplierCatalogItemsUseCase(_FakeRepo()).execute("municipalities")

    def test_returns_items_and_has_more(self):
        result = ListSupplierCatalogItemsUseCase(
            _FakeRepo(rows=[_row()])
        ).execute("states")
        assert result["catalog"] == "states"
        assert result["items"][0]["code"] == "001"
        assert result["has_more"] is False

    def test_every_registry_kind_is_known(self):
        assert set(SUPPLIER_CATALOG_KINDS) == {
            "states",
            "countries",
            "bacen-countries",
            "payment-conditions",
            "payment-methods",
            "financial-natures",
            "accounting-accounts",
            "municipalities",
            "carriers",
            "segments",
            "administrators",
            "employees",
            "price-tables",
            "customers",
        }

    def test_code_param_rejected_for_non_composite_catalog(self):
        with pytest.raises(ValueError, match="code"):
            ListSupplierCatalogItemsUseCase(_FakeRepo()).execute(
                "states", code="SC"
            )

    def test_code_param_forwarded_for_customers(self):
        repo = _FakeRepo()
        result = ListSupplierCatalogItemsUseCase(repo).execute(
            "customers", code="000001"
        )
        assert result["catalog"] == "customers"
        assert repo.queries  # parametrized A1_COD filter applied
