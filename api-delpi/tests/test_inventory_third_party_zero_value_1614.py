"""GLPI #1614 — materiais de terceiros aparecem, mas não têm impacto em R$.

São testes de contrato SQL sem acesso ao Protheus real. Conferir também
comparação operacional de resumo, detalhes e ranking após deploy.
"""
from __future__ import annotations

from app.domain.quality.refugos.refugos_scope import THIRD_PARTY_PRODUCT_TPMAT as SCRAP_THIRD_PARTY
from app.domain.services.supplies.inventory_adjustment_service import (
    InventoryAdjustmentClassification,
    inventory_adjustment_monetary_value_sql,
)
from app.domain.totvs.protheus_product_types import THIRD_PARTY_PRODUCT_TPMAT
from app.infrastructure.persistence.totvs.supplies_repositories.inventory_adjustment_product_sql import (
    inventory_adjustment_product_apply,
)
from app.infrastructure.persistence.totvs.supplies_repositories.inventory_adjustments_repository import (
    InventoryAdjustmentsRepository,
    _summary_select,
)
from app.infrastructure.persistence.totvs.supplies_repositories.inventory_adjustments_tv_repository import (
    InventoryAdjustmentsTvRepository,
)
from app.infrastructure.persistence.totvs.supplies_repositories.inventory_accuracy_sql import (
    build_events_cte,
)


class _CaptureFinancialQueries(InventoryAdjustmentsRepository):
    def __init__(self):
        self.calls: list[str] = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute_one(self, query, params=()):
        self.calls.append(query)
        return {"total": 0}

    def execute_query(self, query, params=()):
        self.calls.append(query)
        return []


class _CaptureRanking(InventoryAdjustmentsTvRepository):
    def __init__(self):
        self.sql = ""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute_query(self, query, params=()):
        self.sql = query
        return []


def test_product_flag_is_same_domain_constant_as_scrap():
    assert THIRD_PARTY_PRODUCT_TPMAT == SCRAP_THIRD_PARTY == "2"


def test_material_type_value_expression_is_zero_only_for_third_party():
    value = inventory_adjustment_monetary_value_sql()
    assert "SB1V.B1_TPMAT" in value
    assert "= '2' THEN 0" in value
    assert "ELSE ISNULL(SD3.D3_CUSTO1, 0)" in value
    assert "D3_QUANT" not in value
    assert InventoryAdjustmentClassification.MONETARY_VALUE_SQL_EXPRESSION == value
    signed = InventoryAdjustmentClassification.SIGNED_VALUE_SQL_EXPRESSION
    assert f"THEN -{value}" in signed
    assert f"THEN {value}" in signed


def test_ownership_lookup_is_cardinality_safe_and_branch_aware():
    query = inventory_adjustment_product_apply()
    assert "OUTER APPLY" in query and "TOP (1)" in query
    assert "SB1.B1_COD = SD3.D3_COD" in query
    assert "SB1.B1_FILIAL = SD3.D3_FILIAL" in query
    assert "SB1.B1_FILIAL = ''" in query
    assert "SB1.D_E_L_E_T_ = ''" in query
    assert "ORDER BY" in query and "THEN 0 ELSE 1" in query
    assert query.count(") SB1V") == 1
    alias_query = inventory_adjustment_product_apply(movement_alias="D")
    assert "SB1.B1_COD = D.D3_COD" in alias_query


def test_all_inventory_adjustment_summary_brl_aggregates_use_zeroed_value():
    sql = _summary_select("")
    money = InventoryAdjustmentClassification.MONETARY_VALUE_SQL_EXPRESSION
    for column in (
        "gross_adjustment_value", "net_adjustment_value",
        "shortage_value", "surplus_value",
    ):
        assert f"AS {column}" in sql
    assert sql.count(f"ABS({money})") >= 5
    assert "OUTER APPLY" in sql
    # Quantidades e quantidade de ajustes permanecem físicas.
    assert "SD3.D3_QUANT" in sql
    assert "COUNT(*) AS adjustment_count" in sql
    # SB1 sinaliza somente o custo; os movimentos físicos não são filtrados.
    assert "B1_TPMAT" in sql
    assert "D3_QUANT" in sql


def test_paginated_items_keep_third_party_in_list_with_zero_monetary_value():
    subject = _CaptureFinancialQueries()
    subject.fetch_adjustment_items(
        date_start="20261101", date_end_exclusive="20261201",
        branch="02", product_code=None, warehouse=None, nature=None,
        page=1, page_size=50,
    )
    assert len(subject.calls) == 2
    _, select_sql = subject.calls
    assert "SB1V.B1_DESC AS product_description" in select_sql
    assert "AS movement_value" in select_sql
    assert "AS signed_value" in select_sql
    assert "B1_TPMAT" in select_sql
    assert "SD3.D3_QUANT AS quantity" in select_sql
    assert "B1_TPMAT" not in select_sql.split("WHERE", 1)[1].split("ORDER BY", 1)[0]


def test_tv_weekly_ranking_preserves_groups_and_zeroes_brl_before_top():
    subject = _CaptureRanking()
    result = subject.fetch_weekly_product_divergences(
        date_start="20261116", date_end_exclusive="20261118",
        branch="02", warehouse=None, top_limit=5,
    )
    sql = subject.sql
    assert result["items"] == []
    assert "TOP (1)" in sql and "OUTER APPLY" in sql
    assert "SUM(CASE WHEN" in sql
    assert "THEN -ABS(CAST(" in sql
    assert "SB1V.B1_TPMAT" in sql
    assert "ABS(CAST(SD3.D3_QUANT" in sql
    assert "COUNT(*) AS movement_count" in sql
    assert "COUNT(*) OVER () AS total_groups" in sql
    assert sql.index("WITH AGG") < sql.index("SELECT TOP (?)")
    assert "ORDER BY ABS(A.signed_value) DESC" in sql
    assert "GROUP BY RTRIM(SD3.D3_FILIAL), RTRIM(SD3.D3_COD)" in sql
    assert "unpriced_movements" in sql


def test_accuracy_percentage_stays_quantity_based_while_monetary_sums_zero():
    query, params = build_events_cte(
        branches=("01", "02"),
        period_start="20261101", period_end_exclusive="20261201",
    )
    money = inventory_adjustment_monetary_value_sql(movement_alias="D")
    assert f"ABS({money})" in query
    assert "OUTER APPLY" in query and "D.D3_FILIAL" in query
    assert "SUM(CAST(S.B7_QUANT AS DECIMAL(18,6)))" in query
    assert "SUM(CASE WHEN D.D3_TM" in query
    assert "e.counted_quantity" in query
    assert "theoretical_quantity" in query
    assert "B1_TPMAT" not in query.split("WHERE D.D_E_L_E_T_ =", 1)[1]
    assert params == [
        "01", "02", "20261101", "20261201",
        "01", "02", "20261101", "20261201",
    ]
