"""F3-R R3 — SQL+params finais idênticos (api-delpi × BFF) na busca SA2."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def repos():
    sys.path.insert(0, str(REPO / "controllership-finance-api"))
    sys.path.insert(0, str(REPO / "shared"))
    sys.path.insert(0, str(REPO / "api-delpi"))
    # Avoid real ODBC: patch connection before importing repositories that touch pyodbc at import
    with patch.dict(sys.modules, {"pyodbc": MagicMock()}):
        bff_mod = importlib.import_module(
            "controllership_finance_app.infrastructure.invoice_posting.totvs_supplier_repository"
        )
        api_mod = importlib.import_module(
            "app.infrastructure.persistence.totvs.supplier_repositories.totvs_supplier_repository"
        )
    return api_mod, bff_mod


def _capture_execute(repo_cls, *, query: str = "aa", limit: int = 20):
    calls: list[tuple] = []

    class FakeRepo(repo_cls):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def execute_query(self, sql, params=()):
            calls.append((sql, params))
            return []

    FakeRepo().search_suppliers(query=query, limit=limit)
    assert calls, "execute_query não foi chamado"
    return calls[0]


def test_supplier_search_sql_and_params_identical(repos) -> None:
    api_mod, bff_mod = repos
    # Locate class name
    api_cls = api_mod.TotvsSupplierRepository
    bff_cls = bff_mod.TotvsSupplierRepository
    sql_api, params_api = _capture_execute(api_cls)
    sql_bff, params_bff = _capture_execute(bff_cls)
    assert "".join(sql_api.split()) == "".join(sql_bff.split())
    assert params_api == params_bff
