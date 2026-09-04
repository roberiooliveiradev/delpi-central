from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from app.application.use_cases.pedidos_venda_abertos.list_customer_billing_series_use_case import (
    ListCustomerBillingSeriesRequest,
    ListCustomerBillingSeriesUseCase,
)
from app.domain.ports.pedidos_venda_abertos.customer_enrichment_repository_port import (
    CustomerBillingMonthRow,
)
from app.domain.services.pedidos_venda_abertos.billing_series_service import (
    fill_billing_monthly_series,
    month_key_from_protheus,
    period_key_from_protheus,
)
from app.infrastructure.persistence.totvs.pedidos_venda_abertos.customer_billing_series_sql import (
    billing_series_period_expr,
    build_customer_billing_series_sql,
)


def test_month_key_from_protheus() -> None:
    assert month_key_from_protheus("202608") == "2026-08"
    assert month_key_from_protheus("2026-08-15") == "2026-08"
    assert month_key_from_protheus("") is None


def test_period_key_from_protheus_by_grain() -> None:
    assert period_key_from_protheus("20260811", granularity="day") == "2026-08-11"
    assert period_key_from_protheus("20260810", granularity="week") == "2026-08-10"
    assert period_key_from_protheus("202608", granularity="month") == "2026-08"
    assert period_key_from_protheus("2026", granularity="year") == "2026"


def test_fill_billing_monthly_series_pads_zeros() -> None:
    points = fill_billing_monthly_series(
        billed_by_month={"2026-07": 1000.0},
        end=date(2026, 8, 4),
        months=3,
    )
    assert [p.month for p in points] == ["2026-06", "2026-07", "2026-08"]
    assert points[0].value == 0.0
    assert points[1].value == 1000.0
    assert points[1].label == "jul/26"
    assert points[1].date_start == "2026-07-01"
    assert points[1].date_end == "2026-07-31"


def test_billing_series_sql_buckets_by_granularity() -> None:
    month_sql = build_customer_billing_series_sql(
        where_pairs="(D2.D2_CLIENTE = ? AND D2.D2_LOJA = ?)",
        granularity="month",
    )
    day_sql = build_customer_billing_series_sql(
        where_pairs="(D2.D2_CLIENTE = ? AND D2.D2_LOJA = ?)",
        granularity="day",
    )
    week_sql = build_customer_billing_series_sql(
        where_pairs="(D2.D2_CLIENTE = ? AND D2.D2_LOJA = ?)",
        granularity="week",
    )
    assert "LEFT(" in month_sql
    assert ", 6)" in month_sql
    assert billing_series_period_expr("day") in day_sql
    assert "19000101" in week_sql
    assert "GROUP BY" in day_sql
    with pytest.raises(ValueError):
        billing_series_period_expr("hour")


def test_billing_series_sql_applies_product_and_market_recorte() -> None:
    from app.infrastructure.persistence.totvs.pedidos_venda_abertos.customer_billing_series_sql import (
        billing_series_params,
        normalize_billing_series_recorte,
    )

    recorte = normalize_billing_series_recorte(
        product_codes=["90A"],
        product_groups=["3019"],
        market="domestic",
    )
    gross_sql = build_customer_billing_series_sql(
        where_pairs="(D2.D2_CLIENTE = ? AND D2.D2_LOJA = ?)",
        granularity="month",
        nature="gross",
        recorte=recorte,
    )
    assert "D2_TOTAL" in gross_sql or "sale_gross" in gross_sql.lower() or "ISNULL(D2.D2_TOTAL" in gross_sql
    assert "D2.D2_COD IN" in gross_sql
    assert "B1_GRUPO" in gross_sql
    assert "F2_VALBRUT" not in gross_sql
    params = billing_series_params(
        pair_params=["C1", "01"],
        start_date="20260101",
        end_date="20261231",
        nature="gross",
        recorte=recorte,
    )
    assert params[-2:] == ("90A", "3019") or ("90A" in params and "3019" in params)

    net_sql = build_customer_billing_series_sql(
        where_pairs="(D2.D2_CLIENTE = ? AND D2.D2_LOJA = ?)",
        granularity="month",
        nature="net",
        recorte=recorte,
    )
    assert "D2.D2_COD IN" in net_sql
    assert "D1.D1_COD IN" in net_sql


def test_list_customer_billing_series_aggregates_and_fills() -> None:
    repo = MagicMock()
    repo.fetch_billing_monthly_series.return_value = [
        CustomerBillingMonthRow("202607", 100.0),
        CustomerBillingMonthRow("2026-07", 50.0),
    ]
    use_case = ListCustomerBillingSeriesUseCase(repo)

    class _FixedDate(date):
        @classmethod
        def today(cls) -> date:  # type: ignore[override]
            return date(2026, 8, 4)

    with patch(
        "app.application.use_cases.pedidos_venda_abertos.list_customer_billing_series_use_case.date",
        _FixedDate,
    ):
        result = use_case.execute(
            ListCustomerBillingSeriesRequest(
                customers=[("100", "01"), ("100", "01"), ("", "01")],
                months=3,
            )
        )

    assert result.customer_count == 1
    assert result.months == 3
    assert result.granularity == "month"
    assert [p.month for p in result.points] == ["2026-06", "2026-07", "2026-08"]
    assert result.points[1].value == 150.0
    call_kwargs = repo.fetch_billing_monthly_series.call_args.kwargs
    assert call_kwargs["customers"] == [("100", "01")]
    assert call_kwargs["granularity"] == "month"
    payload = result.to_dict()
    assert payload["points"][1]["value"] == 150.0
    assert payload["granularity"] == "month"


def test_list_customer_billing_series_empty_customers_still_returns_months() -> None:
    repo = MagicMock()
    use_case = ListCustomerBillingSeriesUseCase(repo)
    result = use_case.execute(ListCustomerBillingSeriesRequest(customers=[], months=12))
    assert result.customer_count == 0
    assert len(result.points) == 12
    assert all(p.value == 0.0 for p in result.points)
    repo.fetch_billing_monthly_series.assert_not_called()


def test_list_customer_billing_series_day_range_fills_holes() -> None:
    repo = MagicMock()
    repo.fetch_billing_monthly_series.return_value = [
        CustomerBillingMonthRow("20260802", 80.0),
    ]
    use_case = ListCustomerBillingSeriesUseCase(repo)
    result = use_case.execute(
        ListCustomerBillingSeriesRequest(
            customers=[("100", "01")],
            start_date="2026-08-01",
            end_date="2026-08-03",
            granularity="day",
        )
    )
    assert result.granularity == "day"
    assert [p.month for p in result.points] == [
        "2026-08-01",
        "2026-08-02",
        "2026-08-03",
    ]
    assert [p.value for p in result.points] == [0.0, 80.0, 0.0]
    assert repo.fetch_billing_monthly_series.call_args.kwargs["granularity"] == "day"


def test_list_customer_billing_series_rejects_day_window_over_limit() -> None:
    use_case = ListCustomerBillingSeriesUseCase(MagicMock())
    with pytest.raises(ValueError, match="93"):
        use_case.execute(
            ListCustomerBillingSeriesRequest(
                customers=[],
                start_date="2026-01-01",
                end_date="2026-08-01",
                granularity="day",
            )
        )


def test_list_customer_billing_series_operation_id_in_router() -> None:
    router = open(
        "app/interface/http/routes/pedidos_venda_abertos/pedidos_venda_abertos_router.py",
        encoding="utf-8",
    ).read()
    assert "list_customer_billing_series" in router
    assert "/customers/billing-series" in router
    assert "start_date" in router
    assert "granularity" in router
    assert "metric" in router


def test_billing_series_sql_quantity_uses_line_qty_not_note_value() -> None:
    sql = build_customer_billing_series_sql(
        where_pairs="(D2.D2_CLIENTE = ? AND D2.D2_LOJA = ?)",
        granularity="month",
        metric="quantity",
        nature="gross",
    )
    assert "D2_QUANT" in sql
    assert "F2_VALBRUT" not in sql
    assert "mixed_units" in sql


def test_billing_series_sql_quantity_net_subtracts_return_qty() -> None:
    sql = build_customer_billing_series_sql(
        where_pairs="(D2.D2_CLIENTE = ? AND D2.D2_LOJA = ?)",
        granularity="month",
        metric="quantity",
        nature="net",
    )
    assert "D2_QUANT" in sql
    assert "D1_QUANT" in sql
    assert "devolucoes" in sql.lower()


def test_list_customer_billing_series_passes_metric_and_mixed_units() -> None:
    repo = MagicMock()
    repo.fetch_billing_monthly_series.return_value = [
        CustomerBillingMonthRow("202607", 12.5, unit="MI", mixed_units=False),
        CustomerBillingMonthRow("202608", 3.0, unit="PC", mixed_units=False),
    ]
    use_case = ListCustomerBillingSeriesUseCase(repo)
    with patch(
        "app.application.use_cases.pedidos_venda_abertos.list_customer_billing_series_use_case.date"
    ) as mock_date:
        mock_date.today.return_value = date(2026, 8, 15)
        mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)
        result = use_case.execute(
            ListCustomerBillingSeriesRequest(
                customers=[("100", "01")],
                months=2,
                metric="quantity",
                nature="gross",
            )
        )
    assert result.metric == "quantity"
    assert result.mixed_units is True
    assert result.unit is None
    assert repo.fetch_billing_monthly_series.call_args.kwargs["metric"] == "quantity"
    payload = result.to_dict()
    assert payload["supportedMetrics"] == ["value", "quantity"]
    assert payload["mixed_units"] is True
