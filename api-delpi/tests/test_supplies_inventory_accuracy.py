"""Unitários — /supplies/inventory-accuracy (GLPI #1197)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.application.dto.supplies.inventory_accuracy_request import (
    InventoryAccuracyItemsRequest,
    InventoryAccuracyQueryRequest,
)
from app.domain.services.supplies import inventory_accuracy_service as svc
from app.infrastructure.persistence.totvs.supplies_repositories import (
    inventory_accuracy_sql as sql,
)


@pytest.fixture
def client() -> TestClient:
    from fastapi import FastAPI

    from app.interface.http.routes.supplies.inventory_accuracy_router import (
        router,
    )

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_router_exposes_summary_and_items(client: TestClient) -> None:
    from app.interface.http.routes.supplies.inventory_accuracy_router import (
        router,
    )

    paths = {route.path for route in router.routes if hasattr(route, "path")}
    assert router.prefix == "/supplies/inventory-accuracy"
    assert "/supplies/inventory-accuracy/summary" in paths
    assert "/supplies/inventory-accuracy/items" in paths


# --- período de referência ---


def test_month_period_bounds() -> None:
    start, end, ref = svc.month_period("2026-09")
    assert (start, end, ref) == ("20260901", "20261001", "2026-09")
    start, end, ref = svc.month_period("2026-12")
    assert (start, end, ref) == ("20261201", "20270101", "2026-12")
    with pytest.raises(ValueError):
        svc.month_period("2026-13")
    with pytest.raises(ValueError):
        svc.month_period("09-2026")


def test_default_period_is_last_closed_month() -> None:
    period = svc.resolve_accuracy_period(
        month=None,
        start_date=None,
        end_date=None,
        last_closing_date="20260930",
    )
    assert period.kind == "last_closed_month"
    assert period.reference_month == "2026-09"
    assert period.period_start == "20260901"
    assert period.period_end_exclusive == "20261001"
    assert period.closed is True


def test_month_param_period() -> None:
    period = svc.resolve_accuracy_period(
        month="2026-08",
        start_date=None,
        end_date=None,
        last_closing_date="20260930",
    )
    assert period.kind == "month"
    assert period.period_start == "20260801"
    assert period.closed is True


def test_custom_period_inclusive_end() -> None:
    period = svc.resolve_accuracy_period(
        month=None,
        start_date="20260901",
        end_date="20260930",
        last_closing_date="20260930",
    )
    assert period.kind == "custom_period"
    assert period.period_end_exclusive == "20261001"
    assert period.reference_month is None


def test_current_month_not_marked_closed() -> None:
    period = svc.resolve_accuracy_period(
        month="2026-10",
        start_date=None,
        end_date=None,
        last_closing_date="20260930",
    )
    assert period.closed is False


def test_period_requires_dates_together() -> None:
    with pytest.raises(ValueError):
        svc.resolve_accuracy_period(
            month=None,
            start_date="20260901",
            end_date=None,
            last_closing_date=None,
        )
    with pytest.raises(ValueError):
        svc.resolve_accuracy_period(
            month=None,
            start_date="20260930",
            end_date="20260901",
            last_closing_date=None,
        )
    with pytest.raises(ValueError):
        svc.resolve_accuracy_period(
            month=None,
            start_date=None,
            end_date=None,
            last_closing_date=None,
        )


# --- evento oficial ---


def test_classify_event_processed_divergent_and_accurate() -> None:
    assert svc.classify_event(
        count_status="2", has_adjustment=True
    ) == (svc.OUTCOME_DIVERGENT, None)
    assert svc.classify_event(
        count_status="2", has_adjustment=False
    ) == (svc.OUTCOME_ACCURATE, None)


def test_classify_event_pending_is_excluded_not_accurate() -> None:
    outcome, reason = svc.classify_event(
        count_status="1", has_adjustment=False
    )
    assert outcome == svc.OUTCOME_EXCLUDED
    assert reason == svc.REASON_PENDING_PROCESSING
    outcome, reason = svc.classify_event(
        count_status="", has_adjustment=True
    )
    assert outcome == svc.OUTCOME_EXCLUDED


def test_theoretical_from_official_adjustment() -> None:
    # furo RE0: teórico > contado
    assert svc.theoretical_quantity(
        counted=10.0, shortage_quantity=5.0, surplus_quantity=0.0
    ) == 15.0
    # sobra DE0: teórico < contado
    assert svc.theoretical_quantity(
        counted=10.0, shortage_quantity=0.0, surplus_quantity=4.0
    ) == 6.0


def test_accuracy_percentage_and_availability() -> None:
    assert svc.accuracy_percentage(5, 309) == 1.62
    assert svc.accuracy_percentage(0, 0) is None
    assert svc.summarize_availability(
        valid_count=0, evaluable_count=0
    ) == ("unavailable", svc.REASON_NO_COUNTS)
    assert svc.summarize_availability(
        valid_count=10, evaluable_count=0
    ) == ("unavailable", svc.REASON_NO_EVALUABLE)
    assert svc.summarize_availability(
        valid_count=10, evaluable_count=9
    ) == ("ok", None)


# --- DTO ---


def test_request_defaults_and_validation() -> None:
    req = InventoryAccuracyQueryRequest()
    assert req.branches == ("01", "02")
    req2 = InventoryAccuracyItemsRequest(outcome="DIVERGENT")
    assert req2.outcome == "divergent"
    with pytest.raises(ValueError):
        InventoryAccuracyItemsRequest(outcome="bogus")
    with pytest.raises(ValueError):
        InventoryAccuracyQueryRequest(start_date="2026/09/01")


# --- SQL canônico ---


def test_sql_event_key_aggregates_physical_lines() -> None:
    query, params = sql.build_events_cte(
        branches=("01", "02"),
        period_start="20260901",
        period_end_exclusive="20261001",
    )
    assert "SUM(CAST(S.B7_QUANT" in query
    assert (
        "GROUP BY S.B7_FILIAL, S.B7_COD, S.B7_LOCAL, S.B7_DATA" in query
    )
    # pareamento SB7×SD3 pela chave canônica (filial+produto+armazém+data)
    assert "e.count_date = D.D3_EMISSAO" in query
    assert "e.warehouse = D.D3_LOCAL" in query
    # ajuste oficial = doc INVENT, sem estorno
    assert "'INVENT'" in query and "D3_ESTORNO" in query
    # tolerância zero: divergente = existe ajuste
    assert "WHEN a.adjustment_rows IS NULL THEN 'accurate'" in query
    # pendente → excluded, nunca accurate
    assert "'pending_processing'" in query
    # teórico oficial = contado + furo - sobra
    assert "theoretical_quantity" in query
    assert params == ["01", "02", "20260901", "20261001",
                      "01", "02", "20260901", "20261001"]


def test_sql_summary_materializes_once() -> None:
    query, _ = sql.build_summary_queries(
        branches=("01",),
        period_start="20260901",
        period_end_exclusive="20261001",
    )
    assert "SELECT * INTO #evaluated" in query
    assert "DROP TABLE #evaluated" in query
    assert "evaluable_count_total" in query


def test_cancelled_events_counted_separately() -> None:
    query, params = sql.build_cancelled_count_query(
        branches=("01",),
        period_start="20260901",
        period_end_exclusive="20261001",
    )
    assert "D_E_L_E_T_ <> ''" in query
    assert params == ["01", "20260901", "20261001"]


# --- use case (stub) ---


class _StubRepo:
    def fetch_last_closing_date(self, **kwargs):
        return "20260930"

    def fetch_summary(self, **kwargs):
        return {
            "totals": {
                "valid_count_total": 320,
                "evaluable_count_total": 309,
                "accurate_count": 5,
                "divergent_count": 304,
                "excluded_count": 11,
                "excluded_pending_processing": 11,
                "shortage_value_total": 1710000.0,
                "surplus_value_total": 1650000.0,
            },
            "by_branch": [],
        }

    def count_cancelled_events(self, **kwargs):
        return 3


def test_summary_use_case_real_shape() -> None:
    from app.application.use_cases.supplies.get_inventory_accuracy_summary_use_case import (
        GetInventoryAccuracySummaryUseCase,
    )

    result = GetInventoryAccuracySummaryUseCase(_StubRepo()).execute(
        InventoryAccuracyQueryRequest()
    )
    s = result["summary"]
    assert s["valid_count_total"] == 320
    assert s["evaluable_count_total"] == 309
    assert s["accurate_count"] == 5
    assert s["accuracy_percentage"] == 1.62
    assert s["coverage_percentage"] == 96.56
    assert s["status"] == "ok"
    assert s["comparison_source"] == (
        "protheus_mata270_adjustment_decision"
    )
    assert result["reference"]["reference_month"] == "2026-09"
    assert result["reference"]["period_closed"] is True
    assert result["exclusions"]["pending_processing"] == 11
    assert result["exclusions"]["cancelled"] == 3
