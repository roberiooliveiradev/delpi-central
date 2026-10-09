"""Unitários — /supplies/non-moving-stock (GLPI #1197)."""

from __future__ import annotations

import json
from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.application.dto.supplies.non_moving_stock_request import (
    NonMovingStockItemsRequest,
    NonMovingStockQueryRequest,
)
from app.domain.services.supplies import non_moving_stock_service as svc
from app.infrastructure.persistence.totvs.supplies_repositories import (
    non_moving_stock_sql as sql,
)


def _body(response) -> dict:
    return json.loads(response.content.decode())


@pytest.fixture
def client() -> TestClient:
    from fastapi import FastAPI

    from app.interface.http.routes.supplies.non_moving_stock_router import (
        router,
    )

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


# --- rotas ---


def test_router_exposes_summary_and_items(client: TestClient) -> None:
    from app.interface.http.routes.supplies.non_moving_stock_router import (
        router,
    )

    paths = {route.path for route in router.routes if hasattr(route, "path")}
    assert router.prefix == "/supplies/non-moving-stock"
    assert "/supplies/non-moving-stock/summary" in paths
    assert "/supplies/non-moving-stock/items" in paths


# --- janela de consumo (R-03) ---


def test_window_default_is_rolling_12m_to_today() -> None:
    window = svc.resolve_consumption_window(
        start_date=None,
        end_date=None,
        today=date(2026, 10, 9),
    )
    assert window.kind == svc.WINDOW_KIND_ROLLING_12M
    assert window.end == "20261009"
    assert window.start == "20251009"
    assert window.no_consumption_status == svc.STATUS_NO_CONSUMPTION_12M


def test_window_custom_period_uses_distinct_status() -> None:
    window = svc.resolve_consumption_window(
        start_date="2026-07-01".replace("-", ""),
        end_date="2026-09-30".replace("-", ""),
        today=date(2026, 10, 9),
    )
    assert window.kind == svc.WINDOW_KIND_CUSTOM
    assert window.start == "20260701"
    assert window.end == "20260930"
    assert window.no_consumption_status == (
        svc.STATUS_NO_CONSUMPTION_IN_PERIOD
    )


def test_window_requires_both_dates() -> None:
    with pytest.raises(ValueError):
        svc.resolve_consumption_window(
            start_date="20260701", end_date=None
        )
    with pytest.raises(ValueError):
        svc.resolve_consumption_window(
            start_date=None, end_date="20260930"
        )
    with pytest.raises(ValueError):
        svc.resolve_consumption_window(
            start_date="20260930", end_date="20260701"
        )


def test_window_month_rollover() -> None:
    window = svc.resolve_consumption_window(
        start_date=None, end_date=None, today=date(2026, 1, 31)
    )
    assert window.start == "20250131"
    assert window.end == "20260131"


# --- classificação ---


def test_classify_with_consumption() -> None:
    window = svc.resolve_consumption_window(
        start_date=None, end_date=None, today=date(2026, 10, 9)
    )
    assert (
        svc.classify_product(
            coverage_start="20100101",
            last_utilization_in_window="20260401",
            window=window,
        )
        == svc.STATUS_WITH_CONSUMPTION
    )


def test_classify_no_consumption_with_coverage() -> None:
    window = svc.resolve_consumption_window(
        start_date=None, end_date=None, today=date(2026, 10, 9)
    )
    assert (
        svc.classify_product(
            coverage_start="20030101",
            last_utilization_in_window=None,
            window=window,
        )
        == svc.STATUS_NO_CONSUMPTION_12M
    )


def test_classify_insufficient_history() -> None:
    window = svc.resolve_consumption_window(
        start_date=None, end_date=None, today=date(2026, 10, 9)
    )
    # produto criado depois do início da janela
    assert (
        svc.classify_product(
            coverage_start="20260601",
            last_utilization_in_window=None,
            window=window,
        )
        == svc.STATUS_INSUFFICIENT_HISTORY
    )
    # sem evidência nenhuma
    assert (
        svc.classify_product(
            coverage_start=None,
            last_utilization_in_window=None,
            window=window,
        )
        == svc.STATUS_INSUFFICIENT_HISTORY
    )


def test_classify_utilization_in_window_wins_over_coverage() -> None:
    """Produto novo com consumo na janela é WITH_CONSUMPTION (fato observado)."""
    window = svc.resolve_consumption_window(
        start_date=None, end_date=None, today=date(2026, 10, 9)
    )
    assert (
        svc.classify_product(
            coverage_start="20261001",
            last_utilization_in_window="20261009",
            window=window,
        )
        == svc.STATUS_WITH_CONSUMPTION
    )


# --- disponibilidade e percentuais ---


def test_availability_fail_closed() -> None:
    assert svc.summarize_availability(
        eligible_stock_value=0, evaluable_stock_value=0
    ) == ("unavailable", svc.REASON_NO_ELIGIBLE_STOCK)
    assert svc.summarize_availability(
        eligible_stock_value=100, evaluable_stock_value=0
    ) == ("unavailable", svc.REASON_NO_EVALUABLE_STOCK)
    assert svc.summarize_availability(
        eligible_stock_value=100, evaluable_stock_value=50
    ) == ("ok", None)


def test_percentage_guard() -> None:
    assert svc.percentage(10, 100) == 10.0
    assert svc.percentage(0, 0) is None
    assert svc.percentage(None, 100) is None


# --- DTO ---


def test_request_defaults_to_approved_scope() -> None:
    req = NonMovingStockQueryRequest()
    assert req.branches == ("01", "02")
    assert req.warehouses == ("01", "99")
    assert req.start_date is None and req.end_date is None


def test_request_rejects_warehouse_outside_scope() -> None:
    with pytest.raises(ValueError):
        NonMovingStockQueryRequest(warehouses=["50"])
    assert NonMovingStockQueryRequest(warehouses=["99"]).warehouses == (
        "99",
    )


def test_request_dates_normalize_and_validate() -> None:
    req = NonMovingStockItemsRequest(
        start_date="2025-10-09", end_date="2026-10-09"
    )
    assert req.start_date == "20251009"
    assert req.end_date == "20261009"
    with pytest.raises(ValueError):
        NonMovingStockItemsRequest(start_date="09/10/2025")


def test_items_request_turnover_status_validation() -> None:
    req = NonMovingStockItemsRequest(turnover_status="no_consumption_12m")
    assert req.turnover_status == "NO_CONSUMPTION_12M"
    with pytest.raises(ValueError):
        NonMovingStockItemsRequest(turnover_status="bogus")


# --- SQL canônico ---


def test_sql_utilization_rule_net_positive_doc_group() -> None:
    from app.domain.totvs.protheus_internal_movements import (
        effective_utilization_base_predicates,
        effective_utilization_net_quantity_sql,
    )

    net = effective_utilization_net_quantity_sql()
    assert "D3_TM" in net and "D3_QUANT" in net
    preds = effective_utilization_base_predicates()
    joined = " ".join(preds)
    assert "D3_ESTORNO" in joined
    assert "'S'" in joined
    assert "INVENT" in joined

    query, params = sql.build_classified_cte(
        branches=("01", "02"),
        warehouses=("01", "99"),
        window_start="20251009",
        window_end="20261009",
        no_consumption_status="NO_CONSUMPTION_12M",
    )
    # transferência interna: espelho anula o grupo (HAVING net>0)
    assert "HAVING SUM(" in query
    # agrupamento por filial+produto+doc+data
    assert "D3_DOC" in query and "D3_EMISSAO" in query
    # cobertura: SB9 + SD3
    assert "SB9010" in query and "B9_DATA" in query
    # elegível: MP + QATU>0 + CM1 mesmo armazém
    assert "B1_TIPO" in query and "'MP'" in query
    assert "B2_QATU > 0" in query
    assert "B2_CM1" in query
    assert "AVG(" not in query.upper()
    # bloqueio cadastral canônico
    assert "B1_MSBLQL" in query
    # parametrização
    assert params[:4] == ["01", "02", "01", "99"]


def test_sql_summary_materializes_cte_once() -> None:
    query, params = sql.build_summary_queries(
        branches=("01",),
        warehouses=("01", "99"),
        window_start="20251009",
        window_end="20261009",
        no_consumption_status="NO_CONSUMPTION_12M",
    )
    assert query.count("#classified") >= 4
    assert "SELECT * INTO #classified" in query
    assert "DROP TABLE #classified" in query
    assert "GROUP BY turnover_status" in query
    assert "GROUP BY branch" in query


def test_sql_items_filters_and_pagination() -> None:
    query, params = sql.build_items_query(
        branches=("01",),
        warehouses=("01", "99"),
        window_start="20251009",
        window_end="20261009",
        no_consumption_status="NO_CONSUMPTION_12M",
        product_codes=None,
        turnover_status="NO_CONSUMPTION_12M",
        blocked=True,
        sort="stock_value_desc",
        offset=0,
        page_size=50,
    )
    assert "turnover_status = ?" in query
    assert "blocked = ?" in query
    assert "OFFSET 0 ROWS FETCH NEXT 50 ROWS ONLY" in query
    assert params[-2:] == ["NO_CONSUMPTION_12M", 1]


# --- use case (repositório stub) ---


class _StubRepo:
    def fetch_summary(self, **kwargs):
        self.summary_kwargs = kwargs
        return {
            "totals": {
                "row_count": 3,
                "product_count": 2,
                "eligible_stock_value": 1000.0,
                "insufficient_history_stock_value": 200.0,
                "no_consumption_stock_value": 400.0,
                "with_consumption_stock_value": 400.0,
                "blocked_stock_value": 100.0,
                "blocked_no_consumption_stock_value": 50.0,
                "blocked_product_count": 1,
                "with_consumption_count": 1,
                "no_consumption_count": 1,
                "insufficient_history_count": 1,
            },
            "by_status": [],
            "by_branch": [],
        }


def test_summary_use_case_denominators() -> None:
    from app.application.use_cases.supplies.get_non_moving_stock_summary_use_case import (
        GetNonMovingStockSummaryUseCase,
    )

    repo = _StubRepo()
    result = GetNonMovingStockSummaryUseCase(repo).execute(
        NonMovingStockQueryRequest(branches=["01"])
    )
    s = result["summary"]
    assert s["eligible_stock_value"] == 1000.0
    assert s["evaluable_stock_value"] == 800.0
    assert s["non_moving_percentage"] == 50.0
    assert s["coverage_percentage"] == 80.0
    assert s["blocked_stock_value"] == 100.0
    assert s["blocked_no_consumption_stock_value"] == 50.0
    assert s["status"] == "ok"
    assert result["reference"]["window_kind"] == "rolling_12m"
    assert result["reference"]["valuation_reference"] == (
        "sb2_current_snapshot"
    )


def test_summary_use_case_unavailable_when_empty() -> None:
    from app.application.use_cases.supplies.get_non_moving_stock_summary_use_case import (
        GetNonMovingStockSummaryUseCase,
    )

    class _Empty(_StubRepo):
        def fetch_summary(self, **kwargs):
            data = super().fetch_summary(**kwargs)
            for key in (
                "eligible_stock_value",
                "insufficient_history_stock_value",
                "no_consumption_stock_value",
            ):
                data["totals"][key] = 0.0
            return data

    result = GetNonMovingStockSummaryUseCase(_Empty()).execute(
        NonMovingStockQueryRequest()
    )
    assert result["summary"]["status"] == "unavailable"
    assert result["summary"]["unavailable_reason"] == (
        "no_eligible_stock"
    )
    assert result["summary"]["non_moving_percentage"] is None
