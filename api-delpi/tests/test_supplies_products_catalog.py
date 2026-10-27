"""Supplies product catalog — SB1 projection, NCM format status, filters."""

from __future__ import annotations

from app.infrastructure.persistence.totvs.product_repositories.product_repository import (
    ProductRepository,
)
from app.interface.http.routes.supplies import products_router


class _FakeRepo(ProductRepository):
    def __init__(self, rows=None, total=0):
        self.queries: list[tuple[str, tuple]] = []
        self._rows = rows or []
        self._total = total

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute_one(self, query, params=()):
        return {"total": self._total}

    def execute_query(self, query, params=()):
        self.queries.append((query, tuple(params)))
        return self._rows


class TestNcmStatus:
    def test_blank_and_zero_placeholder_are_missing(self):
        assert products_router._ncm_status(None) == "missing"
        assert products_router._ncm_status("") == "missing"
        assert products_router._ncm_status("          ") == "missing"
        assert products_router._ncm_status("00000000") == "missing"

    def test_valid_eight_digit_code_is_present(self):
        assert products_router._ncm_status("74081190") == "present"
        assert products_router._ncm_status("  85444900  ") == "present"

    def test_nonstandard_values_are_malformed(self):
        assert products_router._ncm_status("8544.49.00") == "malformed"
        assert products_router._ncm_status("8544420085") == "malformed"
        assert products_router._ncm_status("85444200 8") == "malformed"
        assert products_router._ncm_status("V") == "malformed"
        assert products_router._ncm_status("1234567") == "malformed"


class TestCatalogItemProjection:
    def test_reduced_projection_and_ncm_status(self):
        item = products_router._catalog_item(
            {
                "code": "FIO-CU-001     ",
                "description": "FIO DE COBRE   ",
                "type": "MP",
                "group_code": "1001",
                "subgroup": "10",
                "unit": "KG",
                "ncm_ipi_position": "74081190  ",
                "active": "1",
                "blocked": "2",
                "warehouse": "99",
                "gross_weight": "1.234",
                "not_in_projection": "x",
            }
        )
        assert item == {
            "code": "FIO-CU-001",
            "description": "FIO DE COBRE",
            "type": "MP",
            "group_code": "1001",
            "subgroup": "10",
            "unit": "KG",
            "ncm_code": "74081190",
            "ncm_status": "present",
            "active": "1",
            "blocked": "2",
        }

    def test_blank_ncm_returns_none_code_and_missing_status(self):
        item = products_router._catalog_item({"ncm_ipi_position": "          "})
        assert item["ncm_code"] is None
        assert item["ncm_status"] == "missing"


class TestRepositoryFilters:
    def test_product_type_and_subgroup_clauses(self):
        repo = _FakeRepo(rows=[], total=0)
        repo.search_products(
            code=None,
            group=None,
            description=None,
            product_type=["MP", "PA"],
            subgroup="10",
        )
        sql, params = repo.queries[0]
        assert "SB1.B1_TIPO IN (?, ?)" in sql
        assert "SB1.B1_SUBGRUP" in sql
        assert list(params[:3]) == ["10", "MP", "PA"]

    def test_no_type_filter_keeps_existing_shape(self):
        repo = _FakeRepo(rows=[], total=0)
        repo.search_products(code="FIO", group=None, description=None)
        sql, params = repo.queries[0]
        assert "B1_TIPO IN" not in sql
        assert "LTRIM(RTRIM(SB1.B1_SUBGRUP))" not in sql
        assert params[0] == "FIO%"

    def test_type_whitespace_and_blank_entries_ignored(self):
        repo = _FakeRepo(rows=[], total=0)
        repo.search_products(
            code=None,
            group=None,
            description=None,
            product_type=[" mp ", ""],
        )
        sql, params = repo.queries[0]
        assert "SB1.B1_TIPO IN (?)" in sql
        assert params[0] == "MP"


class TestRouteValidation:
    def test_invalid_product_type_returns_400(self):
        raw = products_router.search_supplies_products.__wrapped__
        response = raw(product_type="M,TOOLONG")
        assert response.status_code == 400

    def test_valid_type_reaches_use_case(self, monkeypatch):
        captured = {}

        class _Page:
            def to_dict(self):
                return {
                    "items": [
                        {
                            "code": "X",
                            "description": "Y",
                            "type": "MP",
                            "ncm_ipi_position": "74081190",
                        }
                    ],
                    "total": 1,
                }

        class _UC:
            def execute(self, dto):
                captured["dto"] = dto
                return _Page()

        monkeypatch.setattr(
            products_router, "build_search_products_use_case", lambda: _UC()
        )
        raw = products_router.search_supplies_products.__wrapped__
        response = raw(product_type="mp,pa", subgroup="10")
        body = response.body
        assert response.status_code == 200
        assert captured["dto"].product_type == ["MP", "PA"]
        assert captured["dto"].subgroup == "10"
        assert b'"ncm_status":"present"' in body
        assert b"74081190" in body
