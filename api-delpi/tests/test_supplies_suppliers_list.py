"""Supplies supplier list — DTO, repository SQL, use case envelope, route AuthZ."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException

from app.application.dto.supplies.suppliers_request import SuppliersListRequest
from app.application.use_cases.supplies.list_supplies_suppliers_use_case import (
    ListSuppliesSuppliersUseCase,
)
from app.infrastructure.persistence.totvs.supplier_repositories.totvs_supplier_repository import (
    TotvsSupplierRepository,
)


class _FakeRepo(TotvsSupplierRepository):
    def __init__(self, rows=None, total=0):
        self.queries: list[tuple[str, tuple]] = []
        self._rows = rows or []
        self._total = total

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute_one(self, query, params=()):
        self.queries.append((query, tuple(params)))
        return {"total": self._total}

    def execute_query(self, query, params=()):
        self.queries.append((query, tuple(params)))
        return self._rows


def _row(code="000001", store="01"):
    return {
        "supplier_code": f"{code} ",
        "supplier_store": store,
        "supplier_name": " ACME LTDA ",
        "supplier_short_name": "ACME",
        "tax_id": "12.345.678/0001-90",
        "state": "SC",
        "msblql": "1",
    }


class TestRepositorySql:
    def test_company_scope_and_indexes(self):
        repo = _FakeRepo(rows=[_row()], total=1)
        items, total = repo.search_suppliers_paged()
        count_sql, _ = repo.queries[0]
        select_sql, _ = repo.queries[1]
        assert "SA2010" in count_sql
        assert "SA2.A2_FILIAL = ''" in count_sql
        assert "D_E_L_E_T_ = ''" in count_sql
        assert "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY" in select_sql
        assert "ORDER BY SA2.A2_NOME ASC, SA2.A2_COD, SA2.A2_LOJA" in select_sql
        assert total == 1
        assert items[0]["supplier_id"] == "00000101"
        assert items[0]["tax_id"] == "12345678000190"
        assert items[0]["blocked"] is True

    def test_query_expands_all_match_forms(self):
        repo = _FakeRepo()
        repo.search_suppliers_paged(query="acme 02")
        select_sql, params = repo.queries[1]
        assert "SA2.A2_COD LIKE ?" in select_sql
        assert "Latin1_General_CI_AI" in select_sql
        assert "SA2.A2_CGC LIKE ?" in select_sql
        assert "SA2.A2_COD LIKE ? AND SA2.A2_LOJA LIKE ?" in select_sql
        assert params[-2:] == (0, 20)

    def test_filters_state_blocked_and_sort(self):
        repo = _FakeRepo()
        repo.search_suppliers_paged(
            state="sc", blocked=True, sort_by="tax_id", sort_dir="desc",
            page=3, page_size=50,
        )
        select_sql, params = repo.queries[1]
        assert "SA2.A2_EST = ?" in select_sql
        assert "SA2.A2_MSBLQL = '1'" in select_sql
        assert "ORDER BY SA2.A2_CGC DESC" in select_sql
        assert params[-2:] == (100, 50)

    def test_not_blocked_and_default_sort_fallback(self):
        repo = _FakeRepo()
        repo.search_suppliers_paged(blocked=False, sort_by="bogus")
        select_sql, _ = repo.queries[1]
        assert "ISNULL(SA2.A2_MSBLQL, '') <> '1'" in select_sql
        assert "ORDER BY SA2.A2_NOME ASC" in select_sql

    def test_tax_id_exact_digit_match_not_like(self):
        repo = _FakeRepo()
        repo.search_suppliers_paged(tax_id="12.345.678/0001-90")
        count_sql, count_params = repo.queries[0]
        select_sql, select_params = repo.queries[1]
        for sql, params in ((count_sql, count_params), (select_sql, select_params)):
            assert "SA2.A2_CGC LIKE ?" not in sql
            assert "REPLACE" in sql and "SA2.A2_CGC" in sql
        # formatted input is digit-normalized before reaching SQL
        assert "12345678000190" in count_params

    def test_tax_id_is_anded_with_query_not_ored(self):
        repo = _FakeRepo()
        repo.search_suppliers_paged(query="acme", tax_id="12345678000190")
        select_sql, _ = repo.queries[1]
        assert ") AND REPLACE" in select_sql

    def test_no_tax_id_keeps_prior_shape(self):
        repo = _FakeRepo()
        repo.search_suppliers_paged(query="acme")
        select_sql, _ = repo.queries[1]
        assert "REPLACE" not in select_sql


class TestDto:
    def test_rejects_short_query(self):
        with pytest.raises(ValueError):
            SuppliersListRequest(query="a")

    def test_rejects_invalid_sort(self):
        with pytest.raises(ValueError):
            SuppliersListRequest(sort_by="sql_injection")
        with pytest.raises(ValueError):
            SuppliersListRequest(sort_dir="sideways")

    def test_normalizes_state_and_clamps(self):
        req = SuppliersListRequest(state=" sc ", page=0, page_size=500)
        assert req.state == "SC"
        assert req.page == 1
        assert req.page_size == 100

    def test_tax_id_digit_normalization(self):
        req = SuppliersListRequest(tax_id="12.345.678/0001-90")
        assert req.tax_id == "12345678000190"

    def test_tax_id_rejects_bad_length(self):
        with pytest.raises(ValueError):
            SuppliersListRequest(tax_id="123")
        with pytest.raises(ValueError):
            SuppliersListRequest(tax_id="123456780001955")


class TestUseCase:
    def test_paged_envelope(self):
        repo = Mock()
        repo.search_suppliers_paged.return_value = (
            [{"supplier_id": "00000101", "supplier_name": "ACME"}],
            41,
        )
        out = ListSuppliesSuppliersUseCase(repo).execute(
            SuppliersListRequest(page=2, page_size=20, query="acme")
        )
        assert out["page"] == 2 and out["total"] == 41 and out["total_pages"] == 3
        assert out["items"][0]["supplier_id"] == "00000101"
        assert out["scope"] == {"company": "01", "table": "SA2010"}
        repo.search_suppliers_paged.assert_called_once()


class TestRouteAuthZ:
    def _request(self, *, s2s=None):
        headers = {}
        if s2s is not None:
            headers["X-Delpi-Service-Authorization"] = s2s
        return SimpleNamespace(headers=headers, state=SimpleNamespace())

    def _run(self, request, *, validator=None, user=None):
        from app.interface.http import s2s_service_access
        from app.interface.http.routes.supplies import suppliers_router

        patches = [
            patch.object(s2s_service_access, "get_request", return_value=request),
            patch.object(s2s_service_access, "resolve_user_context", return_value=user),
            patch("delpi_auth.authorization.resolve_user_context", return_value=user),
        ]
        if validator is not None:
            patches.append(
                patch.object(
                    s2s_service_access.ServiceTokenValidator,
                    "from_env",
                    return_value=validator,
                )
            )
        patches.append(
            patch.object(
                suppliers_router,
                "build_list_supplies_suppliers_use_case",
                return_value=Mock(
                    execute=Mock(
                        return_value={
                            "items": [],
                            "page": 1,
                            "page_size": 20,
                            "total": 0,
                            "total_pages": 0,
                        }
                    )
                ),
            )
        )
        for p in patches:
            p.start()
        try:
            return suppliers_router.list_supplies_suppliers(
                query=None, state=None, blocked=None, tax_id=None,
                page=1, page_size=20,
                sort_by="supplier_name", sort_dir="asc",
            )
        finally:
            for p in reversed(patches):
                p.stop()

    def test_s2s_supplies_api_allowed(self):
        from delpi_auth.service_identity import ServiceIdentity

        validator = Mock()
        validator.validate.return_value = ServiceIdentity(
            client_id="supplies-api",
            subject="svc",
            scopes=frozenset({"suppliers.read"}),
            audience=("api-delpi",),
            issuer="iss",
        )
        resp = self._run(self._request(s2s="Bearer tok"), validator=validator)
        assert resp.status_code == 200
        validator.validate.assert_called_once()

    def test_user_permission_path(self):
        user = SimpleNamespace(
            id="u1", is_superadmin=False,
            permissions=["api-delpi.access"],
        )
        resp = self._run(self._request(), user=user)
        assert resp.status_code == 200

    def test_user_without_permission_denied(self):
        user = SimpleNamespace(id="u1", is_superadmin=False, permissions=[])
        with pytest.raises(Exception, match="Forbidden"):
            self._run(self._request(), user=user)

    def test_legacy_service_principal_denied(self):
        user = SimpleNamespace(
            id="svc", is_superadmin=True, permissions=["*"],
            principal_type="service",
        )
        with pytest.raises(HTTPException) as exc:
            self._run(self._request(), user=user)
        assert exc.value.status_code == 403

    def test_wrong_client_denied(self):
        from delpi_auth.service_errors import ServiceClientDeniedError

        validator = Mock()
        validator.validate.side_effect = ServiceClientDeniedError()
        with pytest.raises(HTTPException) as exc:
            self._run(self._request(s2s="Bearer tok"), validator=validator)
        assert exc.value.status_code == 403

    def test_insufficient_scope_denied(self):
        from delpi_auth.service_errors import ServiceScopeDeniedError

        validator = Mock()
        validator.validate.side_effect = ServiceScopeDeniedError()
        with pytest.raises(HTTPException) as exc:
            self._run(self._request(s2s="Bearer tok"), validator=validator)
        assert exc.value.status_code == 403
