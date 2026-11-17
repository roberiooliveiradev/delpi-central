"""GLPI #1615: saldo líquido por filial e produto no ranking do GR Diário.

A agregação real acontece no SQL Server, antes do TOP. Estes testes
verificam seu contrato e o mapeamento de resultados agregados sem SQL Server.
"""
from __future__ import annotations

import pytest

from app.infrastructure.persistence.totvs.supplies_repositories.inventory_adjustments_tv_repository import (
    InventoryAdjustmentsTvRepository,
    _net_nature,
)


class CaptureConsolidatedRanking(InventoryAdjustmentsTvRepository):
    def __init__(self, rows):
        self.rows = rows
        self.sql = None
        self.params = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute_query(self, sql, params):
        self.sql = sql
        self.params = params
        return self.rows


def _row(*, quantity="-20.000000", value="-100.000000", branch="02",
         warehouse_count=2, total_groups=7):
    # O SQL entrega UMA linha agregada para o produto em todos os armazéns;
    # exemplo: armazém 01 = falta 100 e R$500, armazém 99 = sobra 80 e R$400.
    return {
        "branch": branch, "product_code": "9026-1001",
        "product_description": "Cabo", "unit": "UN",
        "movement_count": 2, "warehouse_count": warehouse_count,
        "shortage_count": 1, "surplus_count": 1,
        "signed_quantity": quantity, "signed_value": value,
        "unpriced_movements": 0, "total_groups": total_groups,
    }


def _fetch(repo, *, branch="02", warehouse=None, top_limit=5):
    return repo.fetch_weekly_product_divergences(
        date_start="20261101", date_end_exclusive="20261118",
        branch=branch, warehouse=warehouse, top_limit=top_limit,
    )


def test_product_balances_shortages_and_surpluses_across_warehouses():
    repo = CaptureConsolidatedRanking([_row()])
    result = _fetch(repo)
    assert result["total_groups"] == 7
    assert result["returned"] == 1
    assert result["truncated"] is True
    item = result["items"][0]
    assert item["product_code"] == "9026-1001"
    assert item["branch"] == "02"
    assert item["warehouse"] == "Todos"
    assert item["warehouse_count"] == 2
    assert item["movement_count"] == 2
    assert item["shortage_count"] == 1
    assert item["surplus_count"] == 1
    assert item["quantity"] == 20
    assert item["signed_quantity"] == -20
    assert item["value_brl"] == 100
    assert item["signed_value_brl"] == -100
    assert item["nature"] == "shortage"
    assert item["nature_label"] == "Falta"
    assert item["quantity_nature_label"] == "Falta"
    assert item["financial_nature_label"] == "Falta"


def test_sql_aggregates_by_branch_product_not_warehouse_or_nature():
    repo = CaptureConsolidatedRanking([_row()])
    _fetch(repo)
    sql = repo.sql
    assert sql is not None
    cte = sql.split("WITH AGG AS (", 1)[1].split(")\n        SELECT TOP (?)", 1)[0]
    assert "GROUP BY RTRIM(SD3.D3_FILIAL), RTRIM(SD3.D3_COD)" in cte
    group_by = cte.rsplit("GROUP BY", 1)[1]
    assert "D3_LOCAL" not in group_by
    assert "D3_CF" not in group_by
    assert "COUNT(DISTINCT RTRIM(SD3.D3_LOCAL))" in cte
    assert "ABS(CAST(SD3.D3_QUANT AS DECIMAL(28, 6)))" in cte
    assert "THEN -ABS(CAST(" in cte and "THEN ABS(CAST(" in cte
    assert "SB1V.B1_TPMAT" in cte
    assert "D3_DOC" in cte and "D3_ESTORNO" in cte
    assert "COUNT(*) OVER () AS total_groups" in sql
    assert "ORDER BY ABS(A.signed_value) DESC, ABS(A.signed_quantity) DESC" in sql
    assert sql.index("GROUP BY RTRIM(SD3.D3_FILIAL)") < sql.index("SELECT TOP (?)")


def test_net_ranking_applies_filters_before_group_and_top_after_group():
    repo = CaptureConsolidatedRanking([])
    result = _fetch(repo, branch="01", warehouse="99", top_limit=1)
    assert result == {"items": [], "total_groups": 0, "returned": 0, "truncated": False}
    sql = repo.sql
    assert sql is not None
    assert "SD3.D3_FILIAL = ?" in sql
    assert "SD3.D3_LOCAL = ?" in sql
    assert repo.params[-1] == 1
    assert "20261101" in repo.params
    assert "20261118" in repo.params
    assert "01" in repo.params
    assert "99" in repo.params


def test_explicit_warehouse_filter_is_retained_as_scope_not_new_group():
    repo = CaptureConsolidatedRanking([_row(warehouse_count=1)])
    result = _fetch(repo, warehouse="01")
    item = result["items"][0]
    assert item["warehouse"] == "01"
    assert item["warehouse_count"] == 1


@pytest.mark.parametrize("quantity,value,expected", [
    (20.0, 100.0, ("surplus", "Sobra", "Sobra", "Sobra")),
    (-20.0, -100.0, ("shortage", "Falta", "Falta", "Falta")),
    (0.0, 0.0, ("balanced", "Compensado", "Compensado", "Compensado")),
    (-20.0, 0.0, ("shortage", "Falta (qtd.; R$ 0)", "Falta", "Compensado")),
    (20.0, -100.0, ("shortage", "Falta (R$) / Sobra (qtd.)", "Sobra", "Falta")),
    (-20.0, 100.0, ("surplus", "Sobra (R$) / Falta (qtd.)", "Falta", "Sobra")),
])
def test_balance_nature_does_not_hide_financial_physical_sign_mismatch(
    quantity, value, expected,
):
    assert _net_nature(quantity=quantity, value=value) == expected


def test_total_compensation_stays_as_one_visible_product():
    repo = CaptureConsolidatedRanking([_row(quantity="0", value="0", total_groups=1)])
    result = _fetch(repo)
    assert result["items"][0]["signed_quantity"] == 0
    assert result["items"][0]["signed_value_brl"] == 0
    assert result["items"][0]["nature_label"] == "Compensado"
    assert result["total_groups"] == 1


def test_third_party_with_nonzero_physical_difference_remains_zero_brl():
    repo = CaptureConsolidatedRanking([_row(quantity="-10", value="0")])
    result = _fetch(repo)
    item = result["items"][0]
    assert item["quantity"] == 10
    assert item["signed_quantity"] == -10
    assert item["signed_value_brl"] == 0
    assert item["value_brl"] == 0
    assert item["nature_label"] == "Falta (qtd.; R$ 0)"


def test_value_and_quantity_rankings_follow_post_consolidation_value():
    repo = CaptureConsolidatedRanking([_row(quantity="80", value="-200")])
    item = _fetch(repo)["items"][0]
    assert item["quantity"] == 80
    assert item["signed_quantity"] == 80
    assert item["value_brl"] == 200
    assert item["signed_value_brl"] == -200
    assert item["nature_label"] == "Falta (R$) / Sobra (qtd.)"


@pytest.mark.parametrize("invalid", (0, 51, -1))
def test_top_limit_remains_bounded(invalid):
    repo = CaptureConsolidatedRanking([])
    with pytest.raises(ValueError):
        _fetch(repo, top_limit=invalid)
    assert repo.sql is None
