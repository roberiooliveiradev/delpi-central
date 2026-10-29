"""Export use case: single engine, honest gating, metadata header."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

import pytest

from app.application.dto.financeiro_stock_inventory.stock_inventory_request import (
    StockInventoryQueryRequest,
)
from app.application.security.stock_inventory_scope import (
    StockInventoryScope,
    StockInventoryScopeUnavailableError,
    UnresolvedStockInventoryScopeResolver,
)
from app.application.use_cases.financeiro_stock_inventory.export_stock_inventory_use_case import (
    ExportStockInventoryUseCase,
    StockInventoryExportTruncatedError,
    StockInventoryNotExportableError,
)
from app.application.use_cases.financeiro_stock_inventory.get_stock_inventory_use_case import (
    GetStockInventoryUseCase,
)


@dataclass
class _ResolvedResolver:
    def resolve(self, *, user_subject):
        return StockInventoryScope(resolved=True, reason="test")


class _FakeRepository:
    def __init__(self, presence=None, rows=None, totals=None, p7=None,
                 wip=None, by_type=None, by_warehouse=None):
        self.presence = presence or {}
        self.rows = rows or []
        self._totals = totals or {}
        self._p7 = p7 or {}
        self._wip = wip or []
        self.by_type = by_type or []
        self.by_warehouse = by_warehouse or []
        self.page_size_seen = None

    def snapshot_branch_counts(self, **kwargs):
        return self.presence

    def totals(self, **kwargs):
        return self._totals

    def list_items(self, *, page_size=None, **kwargs):
        self.page_size_seen = page_size
        return self.rows

    def summary_by_type(self, **kwargs):
        return self.by_type

    def summary_by_warehouse(self, **kwargs):
        return self.by_warehouse

    def p7_totals(self, **kwargs):
        return self._p7

    def work_in_process_by_type(self, **kwargs):
        return self._wip


def _request(**overrides):
    params = {"period": "2026-09"}
    params.update(overrides)
    return StockInventoryQueryRequest.from_query(**params)


def _export_request(**overrides):
    params = {"period": "2026-09", "page_size": 50000}
    params.update(overrides)
    return StockInventoryQueryRequest.from_query(**params)


def _use_case(repo, resolver=None):
    return ExportStockInventoryUseCase(
        get_use_case=GetStockInventoryUseCase(
            repository=repo, scope_resolver=resolver or _ResolvedResolver()
        )
    )


_ROW = {
    "product_code": "P1",
    "description": "Item",
    "product_type": "MP",
    "product_group": "1000",
    "unit": "KG",
    "warehouse": "01",
    "branch_code": "01",
    "historical_quantity": Decimal("10"),
    "historical_stock_value": Decimal("50"),
}

_P7 = {
    "stock_value": Decimal("50"),
    "process_physical_value": Decimal("0"),
}


def _csv_text(result: dict) -> str:
    return result["stream"].getvalue().decode("utf-8-sig")


def test_export_scope_unresolved_is_fail_closed():
    use_case = _use_case(
        _FakeRepository(), resolver=UnresolvedStockInventoryScopeResolver()
    )
    with pytest.raises(StockInventoryScopeUnavailableError):
        use_case.execute(_export_request(), user_subject="user-1")


def test_export_source_missing_refused():
    use_case = _use_case(_FakeRepository(presence={}))
    with pytest.raises(StockInventoryNotExportableError):
        use_case.execute(_export_request(branch="01"), user_subject="u")


def test_export_truncated_population_refused():
    repo = _FakeRepository(
        presence={"01": 5},
        rows=[],
        totals={"item_count": 5, "total_value": Decimal("0")},
        p7=_P7,
    )
    with pytest.raises(StockInventoryExportTruncatedError):
        _use_case(repo).execute(_export_request(), user_subject="u")


def test_export_csv_metadata_and_items():
    repo = _FakeRepository(
        presence={"01": 1},
        rows=[_ROW],
        totals={"item_count": 1, "total_value": Decimal("50")},
        p7=_P7,
    )
    result = _use_case(repo).execute(
        _export_request(branch="01", report_scope="mp_pi_pa"),
        user_subject="ana@delpi.com.br",
    )
    assert result["filename"] == "p7-inventory-2026-09-01-mp_pi_pa.csv"
    assert result["exported_count"] == 1
    assert repo.page_size_seen == 50000

    text = _csv_text(result)
    assert "# competencia=2026-09" in text
    assert "# filial=01" in text
    assert "# escopo=mp_pi_pa" in text
    assert "# escopo_rotulo=Somente MP, PI e PA" in text
    assert "# produtor_oficial=matr460" in text
    assert "# parity_state=PENDING" in text
    assert "# oficial=false" in text
    assert "DOCUMENTO NAO OFICIAL" in text
    assert "# gerado_por=ana@delpi.com.br" in text
    assert "# hash_conteudo_sha256=" in text
    assert "# total_geral=" in text
    assert "P1" in text


def test_export_csv_neutralizes_formula_injection():
    repo = _FakeRepository(
        presence={"01": 1},
        rows=[
            dict(_ROW, description="=1+1"),
            dict(
                _ROW,
                product_code="-CMD",
                product_type="@x",
                warehouse="\t01",
            ),
        ],
        totals={"item_count": 2, "total_value": Decimal("100")},
        p7=_P7,
    )
    result = _use_case(repo).execute(
        _export_request(branch="01"), user_subject="u"
    )
    text = _csv_text(result)
    assert "'=1+1" in text
    assert "'-CMD" in text
    assert "'@x" in text
    # Numeric columns stay untouched.
    assert ",10.0000,50.0000" in text


def test_export_incomplete_marks_missing_branches():
    repo = _FakeRepository(
        presence={"01": 1},
        rows=[_ROW],
        totals={"item_count": 1, "total_value": Decimal("50")},
        p7=_P7,
    )
    result = _use_case(repo).execute(_export_request(), user_subject="u")
    text = _csv_text(result)
    assert "# status=incomplete" in text
    assert "# filiais_ausentes=02" in text
    assert "exportacao parcial" in text
